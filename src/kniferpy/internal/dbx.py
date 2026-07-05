"""SQL query builder and database utilities.

Ports knifer-go's internal/db with Python-idiomatic mappings:

- Go database/sql -> Python DB-API 2.0
- Go generics -> Python type hints with generics
- Go functional options -> callable configurators

Errors use kniferpy.verr types with codes knifer.db.<reason>.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Generic, Sequence, TypeVar

from kniferpy.verr import KniferError


class Dialect(IntEnum):
    UNKNOWN = 0
    QUESTION = 1  # ? placeholders
    MYSQL = 2
    SQLITE = 3
    POSTGRES = 4
    SQL_SERVER = 5
    ORACLE = 6
    CLICK_HOUSE = 7


# Dialect constants (Go-style names)
DialectUnknown = Dialect.UNKNOWN
DialectQuestion = Dialect.QUESTION
DialectMySQL = Dialect.MYSQL
DialectSQLite = Dialect.SQLITE
DialectPostgres = Dialect.POSTGRES
DialectSQLServer = Dialect.SQL_SERVER
DialectOracle = Dialect.ORACLE
DialectClickHouse = Dialect.CLICK_HOUSE


class Direction(IntEnum):
    ASC = 0
    DESC = 1


AscDirection = Direction.ASC
DescDirection = Direction.DESC


class LogicalOperator(IntEnum):
    AND = 0
    OR = 1


And = LogicalOperator.AND
Or = LogicalOperator.OR


# --- base types ---------------------------------------------------------------

T = TypeVar("T")


@dataclass
class Order:
    field: str
    direction: Direction = Direction.ASC


@dataclass
class Page:
    number: int
    size: int
    orders: list[Order] = field(default_factory=list)

    @property
    def offset(self) -> int:
        if self.number <= 0:
            return 0
        return (self.number - 1) * self.size

    def limit(self) -> int:
        """Return the page size (Go compat)."""
        return self.size


@dataclass
class PageResult(Generic[T]):
    page: Page
    total: int
    items: list[T]

    def is_first(self) -> bool:
        """Return whether this is the first page (Go compat)."""
        return self.page.number <= 1

    def is_last(self) -> bool:
        """Return whether this is the last page (Go compat)."""
        if self.page.size <= 0:
            return True
        return self.page.number * self.page.size >= self.total

    @property
    def page_size(self) -> int:
        """Return the page size (Go compat)."""
        return self.page.size

    @property
    def total_page(self) -> int:
        """Return the total number of pages (Go compat)."""
        if self.page.size <= 0:
            return 0
        return (self.total + self.page.size - 1) // self.page.size


@dataclass
class Column:
    name: str
    data_type: str = ""
    nullable: bool = False
    auto_increment: bool = False
    primary_key: bool = False


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)


class Entity:
    """Base interface for database entity mapping."""

    def set(self, field: str, value: Any) -> Entity:
        setattr(self, field, value)
        return self

    def set_if_not_nil(self, field: str, value: Any) -> Entity:
        if value is not None:
            setattr(self, field, value)
        return self

    def select(self, *fields: str) -> Entity:
        return self

    def filter(self, *fields: str) -> Entity:
        return self

    def remove(self, *fields: str) -> Entity:
        return self


Condition = Callable[[Dialect], tuple[str, list[Any]]]
"""Condition is a function that builds condition SQL and argument list for a given dialect."""


@dataclass
class NamedSQL:
    sql: str
    args: list[Any]


# --- errors -------------------------------------------------------------------


class DBError(KniferError):
    """Database error with error code and optional cause."""

    def __init__(self, message: str, code: str = "knifer.db.error", cause: BaseException | None = None) -> None:
        super().__init__(message=message, code=code)
        self.cause = cause

    def __str__(self) -> str:
        if self.cause is not None:
            return f"{self.message}: {self.cause}"
        return self.message

    def unwrap(self) -> BaseException | None:
        """Return the wrapped cause error (Go compat)."""
        return self.cause


def new_db_error(format_str: str, *args: Any) -> DBError:
    msg = (format_str % args) if args else format_str
    return DBError(message=msg, code="knifer.db.error")


def wrap_db_error(cause: BaseException, format_str: str, *args: Any) -> DBError:
    msg = (format_str % args) if args else format_str
    return DBError(message=msg, code="knifer.db.error", cause=cause)


# --- builder ------------------------------------------------------------------


@dataclass
class SQLBuilder:
    _sql: str = ""
    _is_raw: bool = False
    _select: list[str] = field(default_factory=list)
    _from: list[str] = field(default_factory=list)
    _where: list[str] = field(default_factory=list)
    _conditions: list[Condition] = field(default_factory=list)
    _group_by: list[str] = field(default_factory=list)
    _having: list[str] = field(default_factory=list)
    _order_by: list[Order] = field(default_factory=list)
    _limit: int | None = None
    _offset: int | None = None
    _is_insert: bool = False
    _insert_entity: Entity | None = None
    _delete_from: str = ""
    _update_table: str = ""
    _update_set: list[tuple[str, Any]] = field(default_factory=list)

    def to_sql(self, dialect: Dialect) -> tuple[str, list[Any]]:
        args: list[Any] = []
        parts: list[str] = []

        if self._is_raw:
            return self._sql, args

        if self._is_insert:
            if self._insert_entity is not None and hasattr(self._insert_entity, "__table__"):
                table_name = self._insert_entity.__table__
                parts.append(f"INSERT INTO {table_name}")
            else:
                parts.append("INSERT")
            # Columns and values handled by entity introspection
            return " ".join(parts), args
        if self._delete_from:
            parts.append(f"DELETE FROM {self._delete_from}")
        elif self._update_table:
            parts.append(f"UPDATE {self._update_table} SET ")
            set_clauses: list[str] = []
            for field_name, _ in self._update_set:
                set_clauses.append(f"{field_name} = {_placeholder(dialect)}")
                args.extend(val for _, val in self._update_set)
            parts.append(", ".join(set_clauses))
        elif self._select:
            parts.append(f"SELECT {', '.join(self._select)} FROM {', '.join(self._from)}")
        else:
            raise DBError("invalid builder state: no SELECT/INSERT/UPDATE/DELETE")

        if self._where or self._conditions:
            where_parts: list[str] = list(self._where)
            for cond in self._conditions:
                cond_sql, cond_args = cond(dialect)
                where_parts.append(cond_sql)
                args.extend(cond_args)
            parts.append("WHERE " + " AND ".join(where_parts))

        if self._group_by:
            parts.append(f"GROUP BY {', '.join(self._group_by)}")
        if self._having:
            parts.append(f"HAVING {' AND '.join(self._having)}")
        if self._order_by:
            order_clauses: list[str] = []
            for order in self._order_by:
                dir_sql = "ASC" if order.direction == Direction.ASC else "DESC"
                order_clauses.append(f"{order.field} {dir_sql}")
            parts.append(f"ORDER BY {', '.join(order_clauses)}")
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        if self._offset is not None:
            parts.append(f"OFFSET {self._offset}")

        return " ".join(parts), args

    def sql(self, dialect: Dialect) -> tuple[str, list[Any]]:
        """Go-compat alias for to_sql()."""
        return self.to_sql(dialect)


# --- builder factories --------------------------------------------------------


def new_builder() -> SQLBuilder:
    return SQLBuilder()


def raw(sql: str) -> SQLBuilder:
    b = new_builder()
    b._sql = sql
    b._is_raw = True
    return b


def select(fields: Sequence[str]) -> SQLBuilder:
    b = new_builder()
    b._select.extend(fields)
    return b


def insert(entity: Entity) -> SQLBuilder:
    b = new_builder()
    b._is_insert = True
    b._insert_entity = entity
    return b


def update(table: str) -> SQLBuilder:
    b = new_builder()
    b._update_table = table
    return b


def delete(table: str) -> SQLBuilder:
    b = new_builder()
    b._delete_from = table
    return b


def set_field(builder: SQLBuilder, field: str, value: Any) -> SQLBuilder:
    builder._update_set.append((field, value))
    return builder


def from_tables(builder: SQLBuilder, tables: Sequence[str]) -> SQLBuilder:
    builder._from.extend(tables)
    return builder


def where(builder: SQLBuilder, cond_sql: str) -> SQLBuilder:
    builder._where.append(cond_sql)
    return builder


def add_condition(builder: SQLBuilder, cond: Condition) -> SQLBuilder:
    builder._conditions.append(cond)
    return builder


def group_by(builder: SQLBuilder, fields: Sequence[str]) -> SQLBuilder:
    builder._group_by.extend(fields)
    return builder


def having(builder: SQLBuilder, cond_sql: str) -> SQLBuilder:
    builder._having.append(cond_sql)
    return builder


def order_by(builder: SQLBuilder, order: Order) -> SQLBuilder:
    builder._order_by.append(order)
    return builder


def limit(builder: SQLBuilder, n: int) -> SQLBuilder:
    if n > 0:
        builder._limit = n
    return builder


def offset(builder: SQLBuilder, n: int) -> SQLBuilder:
    if n >= 0:
        builder._offset = n
    return builder


# --- conditions ---------------------------------------------------------------


def _placeholder(dialect: Dialect) -> str:
    if dialect == Dialect.QUESTION:
        return "?"
    if dialect in (Dialect.MYSQL, Dialect.SQLITE):
        return "?"
    if dialect in (Dialect.POSTGRES, Dialect.ORACLE, Dialect.CLICK_HOUSE):
        return "$%d"  # caller will handle numbering
    if dialect == Dialect.SQL_SERVER:
        return "@p%d"
    return "?"


def _wrap_condition(
    op: str,
    field: str,
    value: Any,
) -> Condition:
    def _cond(dialect: Dialect) -> tuple[str, list[Any]]:
        return f"{field} {op} {_placeholder(dialect)}", [value]
    return _cond


def eq(field: str, value: Any) -> Condition:
    return _wrap_condition("=", field, value)


def ne(field: str, value: Any) -> Condition:
    return _wrap_condition("!=", field, value)


def gt(field: str, value: Any) -> Condition:
    return _wrap_condition(">", field, value)


def gte(field: str, value: Any) -> Condition:
    return _wrap_condition(">=", field, value)


def lt(field: str, value: Any) -> Condition:
    return _wrap_condition("<", field, value)


def lte(field: str, value: Any) -> Condition:
    return _wrap_condition("<=", field, value)


def like(field: str, value: Any) -> Condition:
    return _wrap_condition("LIKE", field, value)


def in_list(field: str, values: Sequence[Any]) -> Condition:
    def _cond(dialect: Dialect) -> tuple[str, list[Any]]:
        placeholders = ", ".join([_placeholder(dialect)] * len(values))
        return f"{field} IN ({placeholders})", list(values)
    return _cond


def between(field: str, begin: Any, end: Any) -> Condition:
    def _cond(dialect: Dialect) -> tuple[str, list[Any]]:
        return f"{field} BETWEEN {_placeholder(dialect)} AND {_placeholder(dialect)}", [begin, end]
    return _cond


def is_null(field: str) -> Condition:
    def _cond(_: Dialect) -> tuple[str, list[Any]]:
        return f"{field} IS NULL", []
    return _cond


def is_not_null(field: str) -> Condition:
    def _cond(_: Dialect) -> tuple[str, list[Any]]:
        return f"{field} IS NOT NULL", []
    return _cond


def and_group(conds: Sequence[Condition]) -> Condition:
    def _cond(dialect: Dialect) -> tuple[str, list[Any]]:
        if not conds:
            return "1=1", []
        parts: list[str] = []
        args: list[Any] = []
        for cond in conds:
            sql, cond_args = cond(dialect)
            parts.append(f"({sql})")
            args.extend(cond_args)
        return " AND ".join(parts), args
    return _cond


def or_group(conds: Sequence[Condition]) -> Condition:
    def _cond(dialect: Dialect) -> tuple[str, list[Any]]:
        if not conds:
            return "1=0", []
        parts: list[str] = []
        args: list[Any] = []
        for cond in conds:
            sql, cond_args = cond(dialect)
            parts.append(f"({sql})")
            args.extend(cond_args)
        return " OR ".join(parts), args
    return _cond


def asc(field: str) -> Order:
    return Order(field, Direction.ASC)


def desc(field: str) -> Order:
    return Order(field, Direction.DESC)


def new_page(number: int, size: int, orders: Sequence[Order] | None = None) -> Page:
    return Page(number=number, size=size, orders=list(orders or []))


def new_page_result(page: Page, total: int, items: list[Any]) -> PageResult[Any]:
    return PageResult(page=page, total=total, items=items)


# --- named parameter parsing -------------------------------------------------


def _extract_named_params(sql: str) -> list[str]:
    pattern = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")
    return pattern.findall(sql)


def parse_named(sql: str, args: dict[str, Any], dialect: Dialect) -> NamedSQL:
    """Convert :named parameters to dialect placeholders with positional args."""
    param_names = _extract_named_params(sql)
    if not param_names:
        return NamedSQL(sql, [])
    result_sql = sql
    result_args: list[Any] = []
    idx = 1
    for name in param_names:
        if name not in args:
            raise DBError(f"named parameter {name!r} not found in args")
        result_args.append(args[name])
        if dialect == Dialect.QUESTION:
            result_sql = result_sql.replace(f":{name}", "?")
        elif dialect in (Dialect.POSTGRES, Dialect.ORACLE, Dialect.CLICK_HOUSE):
            result_sql = result_sql.replace(f":{name}", f"${idx}")
            idx += 1
        elif dialect == Dialect.SQL_SERVER:
            result_sql = result_sql.replace(f":{name}", f"@p{idx}")
            idx += 1
        elif dialect in (Dialect.MYSQL, Dialect.SQLITE):
            result_sql = result_sql.replace(f":{name}", "?")
    return NamedSQL(result_sql, result_args)


# --- dialect and identifier wrapping ------------------------------------------


class Wrapper:
    """Identifier wrapper adds quotes/delimiters around SQL identifiers."""

    def __init__(self, prefix: str, suffix: str) -> None:
        self.prefix = prefix
        self.suffix = suffix

    def wrap(self, name: str) -> str:
        if "." in name:
            parts = name.split(".")
            return ".".join(self.prefix + p + self.suffix for p in parts)
        return self.prefix + name + self.suffix

    def unwrap(self, name: str) -> str:
        """Remove identifier quoting (Go compat)."""
        result = name
        if name.startswith(self.prefix):
            result = result[len(self.prefix):]
        if name.endswith(self.suffix):
            result = result[:-len(self.suffix)]
        return result


def new_wrapper(prefix: str, suffix: str | None = None) -> Wrapper:
    if suffix is None:
        suffix = prefix
    return Wrapper(prefix, suffix)


def wrapper_for_dialect(dialect: Dialect) -> Wrapper:
    if dialect in (Dialect.MYSQL, Dialect.CLICK_HOUSE):
        return new_wrapper("`", "`")
    if dialect == Dialect.POSTGRES:
        return new_wrapper('"', '"')
    if dialect == Dialect.SQL_SERVER:
        return new_wrapper("[", "]")
    return new_wrapper("\"", "\"")


def normalize_dialect(driver_name: str) -> Dialect:
    name = driver_name.lower()
    if name in ("sqlite3", "sqlite"):
        return Dialect.SQLITE
    if name in ("mysql", "pymysql", "mysqlclient"):
        return Dialect.MYSQL
    if name in ("psycopg2", "psycopg", "postgresql", "postgres"):
        return Dialect.POSTGRES
    if name in ("pyodbc", "pymssql"):
        return Dialect.SQL_SERVER
    if name in ("cx_oracle", "oracledb"):
        return Dialect.ORACLE
    return Dialect.UNKNOWN


def is_safe_identifier(name: str) -> bool:
    """Check if name is a safe SQL identifier (letters/digits/underscore only)."""
    return bool(re.fullmatch(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$", name))


# --- connection options ---------------------------------------------------------


SQLOpenFunc = Callable[[str], Any]
"""Signature: (connection_string) -> DB connection"""


@dataclass
class Options:
    dialect: Dialect = Dialect.UNKNOWN
    wrapper: Wrapper | None = None
    max_open_conns: int | None = None
    max_idle_conns: int | None = None
    conn_max_lifetime: int | None = None
    conn_max_idle_time: int | None = None
    sql_open_func: SQLOpenFunc | None = None


def new_options() -> Options:
    return Options()


def with_dialect(d: Dialect) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.dialect = d
    return _apply


def with_wrapper(w: Wrapper) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.wrapper = w
    return _apply


def with_max_open_conns(n: int) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.max_open_conns = n
    return _apply


def with_max_idle_conns(n: int) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.max_idle_conns = n
    return _apply


def with_conn_max_lifetime(d: int) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.conn_max_lifetime = d
    return _apply


def with_conn_max_idle_time(d: int) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.conn_max_idle_time = d
    return _apply


def with_sql_open_func(open_func: SQLOpenFunc) -> Callable[[Options], None]:
    def _apply(opts: Options) -> None:
        opts.sql_open_func = open_func
    return _apply


# --- db/session wrapper ---------------------------------------------------------


@dataclass
class DB:
    """Wrapper around a DB-API 2.0 connection pool."""
    _conn: Any  # DB-API connection or pool
    _dialect: Dialect
    _wrapper: Wrapper

    @property
    def dialect(self) -> Dialect:
        return self._dialect

    @property
    def wrapper(self) -> Wrapper:
        return self._wrapper

    def sql_db(self) -> Any:
        """Return the underlying DB-API connection (Go compat)."""
        return self._conn

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    def ping(self) -> None:
        """Ping the database."""
        cursor = self._conn.execute("SELECT 1")
        cursor.close()

    def exec(self, query: str, *args: Any) -> Any:
        """Execute SQL and return cursor."""
        cursor = self._conn.execute(query, args or ())
        return cursor

    def exec_named(self, query: str, args: dict[str, Any]) -> Any:
        """Execute named-parameter SQL."""
        named = parse_named(query, args, self._dialect)
        return self.exec(named.sql, *named.args)

    def exec_batch(self, query: str, *batches: Sequence[Any]) -> list[Any]:
        """Execute the same SQL with multiple argument sets."""
        results = []
        for batch in batches:
            results.append(self._conn.execute(query, batch))
        return results

    def query_entities(self, query: str, *args: Any) -> list[dict]:
        """Execute SQL and scan rows into dicts."""
        cursor = self._conn.execute(query, args or ())
        return scan_rows(cursor)

    def query_named(self, query: str, args: dict[str, Any]) -> list[dict]:
        """Execute named-parameter SQL and scan rows into dicts."""
        named = parse_named(query, args, self._dialect)
        return self.query_entities(named.sql, *named.args)

    def query_one(self, query: str, *args: Any) -> tuple[dict | None, bool]:
        """Execute SQL and return first row."""
        cursor = self._conn.execute(query, args or ())
        return scan_one(cursor)

    def query_scalar(self, query: str, *args: Any) -> tuple[Any, bool]:
        """Execute SQL and return first column from first row."""
        cursor = self._conn.execute(query, args or ())
        if cursor is None:
            return None, False
        try:
            row = cursor.fetchone()
            if row is None:
                return None, False
            return row[0], True
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def insert(self, entity: Entity) -> Any:
        """Insert entity values."""
        b = insert(entity)
        sql, args = b.to_sql(self._dialect)
        return self._conn.execute(sql, args)

    def insert_get_id(self, entity: Entity) -> int:
        """Insert entity and return last row id."""
        cursor = self.insert(entity)
        return cursor.lastrowid

    def upsert(self, entity: Entity, conflict_fields: list[str], *update_fields: str) -> Any:
        """Insert or update entity on conflict."""
        b = insert(entity)
        sql, args = b.to_sql(self._dialect)
        if self._dialect == Dialect.MYSQL:
            upsert_sql = _build_mysql_upsert(sql, entity, conflict_fields, update_fields, self._wrapper)
        elif self._dialect in (Dialect.POSTGRES, Dialect.SQLITE):
            upsert_sql = _build_pg_upsert(sql, entity, conflict_fields, update_fields, self._wrapper)
        else:
            raise DBError(f"upsert is not implemented for dialect {self._dialect}")
        return self._conn.execute(upsert_sql, args)

    def update(self, entity: Entity, *conds: Condition) -> Any:
        """Update rows matching conditions."""
        table = getattr(entity, "__table__", "unknown")
        b = update(table)
        for f, v in entity.fields.items():
            b = set_field(b, f, v)
        for c in conds:
            b = add_condition(b, c)
        sql, args = b.to_sql(self._dialect)
        return self._conn.execute(sql, args)

    def update_all(self, entity: Entity) -> Any:
        """Update all rows in entity's table."""
        table = getattr(entity, "__table__", "unknown")
        b = update(table)
        for f, v in entity.fields.items():
            b = set_field(b, f, v)
        sql, args = b.to_sql(self._dialect)
        return self._conn.execute(sql, args)

    def delete(self, table: str, *conds: Condition) -> Any:
        """Delete rows matching conditions."""
        if not conds:
            raise DBError("DELETE without conditions is unsafe; use delete_all to affect every row")
        b = delete(table)
        for c in conds:
            b = add_condition(b, c)
        sql, args = b.to_sql(self._dialect)
        return self._conn.execute(sql, args)

    def delete_all(self, table: str) -> Any:
        """Delete all rows from table."""
        b = delete(table)
        sql, args = b.to_sql(self._dialect)
        return self._conn.execute(sql, args)

    def delete_entity(self, entity: Entity) -> Any:
        """Delete rows using entity values as equality conditions."""
        conds = conditions_from_entity(entity)
        return self.delete(getattr(entity, "__table__", "unknown"), *conds)

    def get(self, table: str, field: str, value: Any) -> tuple[dict | None, bool]:
        """Find one row by field equality."""
        b = select(["*"])
        b = from_tables(b, [table])
        b = add_condition(b, eq(field, value))
        sql, args = b.to_sql(self._dialect)
        return self.query_one(sql, *args)

    def find(self, query: SQLBuilder) -> list[dict]:
        """Run a query and return rows."""
        b = select(["*"])
        if query._from:
            b._from = query._from
        if query._conditions:
            b._conditions = query._conditions
        if query._where:
            b._where = query._where
        if query._order_by:
            b._order_by = query._order_by
        if query._limit is not None:
            b._limit = query._limit
        if query._offset is not None:
            b._offset = query._offset
        if query._select:
            b._select = query._select
        sql, args = b.to_sql(self._dialect)
        return self.query_entities(sql, *args)

    def find_all(self, table: str) -> list[dict]:
        """Return all rows from table."""
        b = select(["*"])
        b = from_tables(b, [table])
        return self.find(b)

    def find_by(self, table: str, field: str, value: Any) -> list[dict]:
        """Return rows where field equals value."""
        b = select(["*"])
        b = from_tables(b, [table])
        b = add_condition(b, eq(field, value))
        return self.find(b)

    def find_like(self, table: str, field: str, value: Any, mode: str = "") -> list[dict]:
        """Return rows where field matches LIKE pattern."""
        pattern = build_like_value(str(value))
        b = select(["*"])
        b = from_tables(b, [table])
        b = add_condition(b, like(field, pattern))
        return self.find(b)

    def count(self, table: str, *conds: Condition) -> int:
        """Count rows in table matching conditions."""
        b = select(["COUNT(*)"])
        b = from_tables(b, [table])
        for c in conds:
            b = add_condition(b, c)
        sql, args = b.to_sql(self._dialect)
        result, found = self.query_scalar(sql, *args)
        return int(result) if found else 0

    def page(self, query: SQLBuilder, page: Page) -> PageResult:
        """Run a paged query and count query."""
        b = select(["*"])
        if query._from:
            b = from_tables(b, query._from)
        if query._conditions:
            b._conditions = query._conditions
        if query._where:
            b._where = query._where
        if page.orders:
            for o in page.orders:
                b = order_by(b, o)
        b = limit(b, page.size)
        b = offset(b, page.offset)

        items = self.find(b)

        tables = query._from if query._from else []
        count_b = select(["COUNT(*)"])
        if tables:
            count_b = from_tables(count_b, tables)
        if query._conditions:
            count_b._conditions = query._conditions
        count_sql, count_args = count_b.to_sql(self._dialect)
        result, found = self.query_scalar(count_sql, *count_args)
        total = int(result) if found else 0

        return new_page_result(page, total, items)

    def tx(self, fn: Callable[[Session], Any]) -> Any:
        """Run fn inside a transaction."""
        try:
            self._conn.execute("BEGIN")
            session = Session(_db=self, _conn=self._conn)
            result = fn(session)
            self._conn.commit()
            return result
        except Exception:
            self._conn.rollback()
            raise

    def list_tables(self) -> list[str]:
        """List user tables."""
        if self._dialect == Dialect.SQLITE:
            cursor = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
        raise DBError(f"list_tables is not implemented for dialect {self._dialect}")

    def list_columns(self, table: str) -> list[Column]:
        """List columns for table."""
        if self._dialect == Dialect.SQLITE:
            cursor = self._conn.execute(f"PRAGMA table_info({self._wrapper.wrap(table)})")
            columns = []
            for row in cursor.fetchall():
                columns.append(Column(
                    name=row[1],
                    data_type=row[2],
                    nullable=not row[3],
                    auto_increment=False,
                    primary_key=row[5] > 0,
                ))
            return columns
        raise DBError(f"list_columns is not implemented for dialect {self._dialect}")

    def table_meta(self, table: str) -> Table:
        """Return table metadata with columns and primary keys."""
        cols = self.list_columns(table)
        return Table(name=table, columns=cols)

    def column_names(self, table: str) -> list[str]:
        """Return column names for table."""
        cols = self.list_columns(table)
        return [c.name for c in cols]

    def primary_keys(self, table: str) -> list[str]:
        """Return primary key column names for table."""
        cols = self.list_columns(table)
        return [c.name for c in cols if c.primary_key]


@dataclass
class Session:
    """Active database session (transaction wrapper)."""
    _db: DB
    _conn: Any  # DB-API connection

    @contextlib.contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        try:
            yield self
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def execute(self, query: str, args: Sequence[Any] | None = None) -> Any:
        if args is None:
            args = []
        return self._conn.execute(query, args)

    def query(self, builder: SQLBuilder) -> Any:
        sql, args = builder.to_sql(self._db.dialect)
        return self._conn.execute(sql, args)

    def query_one(self, builder: SQLBuilder, factory: Callable[[Any], T]) -> T | None:
        cursor = self.query(builder)
        row = cursor.fetchone()
        if row is None:
            return None
        return factory(row)

    def query_all(self, builder: SQLBuilder, factory: Callable[[Any], T]) -> list[T]:
        cursor = self.query(builder)
        rows = cursor.fetchall()
        return [factory(row) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def exec(self, query: str, *args: Any) -> Any:
        """Execute SQL in the transaction (Go compat)."""
        return self._conn.execute(query, args or ())

    def exec_named(self, query: str, args: dict[str, Any]) -> Any:
        """Execute named-parameter SQL in the transaction."""
        named = parse_named(query, args, self._db.dialect)
        return self.exec(named.sql, *named.args)

    def exec_batch(self, query: str, *batches: Sequence[Any]) -> list[Any]:
        """Execute the same SQL with multiple argument sets."""
        results = []
        for batch in batches:
            results.append(self._conn.execute(query, batch))
        return results

    def query_entities(self, query: str, *args: Any) -> list[dict]:
        """Execute SQL and scan rows into dicts."""
        cursor = self._conn.execute(query, args or ())
        return scan_rows(cursor)

    def query_one_entity(self, query: str, *args: Any) -> tuple[dict | None, bool]:
        """Execute SQL and return first row."""
        cursor = self._conn.execute(query, args or ())
        return scan_one(cursor)

    def query_scalar(self, query: str, *args: Any) -> tuple[Any, bool]:
        """Execute SQL and return first column from first row."""
        cursor = self._conn.execute(query, args or ())
        if cursor is None:
            return None, False
        try:
            row = cursor.fetchone()
            if row is None:
                return None, False
            return row[0], True
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def insert(self, entity: Entity) -> Any:
        """Insert entity in the transaction."""
        return self._db.insert(entity)

    def upsert(self, entity: Entity, conflict_fields: list[str], *update_fields: str) -> Any:
        """Insert or update entity in the transaction."""
        return self._db.upsert(entity, conflict_fields, *update_fields)

    def update(self, entity: Entity, *conds: Condition) -> Any:
        """Update rows in the transaction."""
        return self._db.update(entity, *conds)

    def update_all(self, entity: Entity) -> Any:
        """Update all rows in the transaction."""
        return self._db.update_all(entity)

    def delete(self, table: str, *conds: Condition) -> Any:
        """Delete rows in the transaction."""
        return self._db.delete(table, *conds)

    def delete_all(self, table: str) -> Any:
        """Delete all rows in the transaction."""
        return self._db.delete_all(table)

    def savepoint(self, name: str) -> None:
        """Create a savepoint."""
        self._conn.execute(f"SAVEPOINT {self._db.wrapper.wrap(name)}")

    def rollback_to(self, name: str) -> None:
        """Roll back to a savepoint."""
        self._conn.execute(f"ROLLBACK TO SAVEPOINT {self._db.wrapper.wrap(name)}")


# ── internal helpers for DB CRUD ────────────────────────────────────────────


def _build_mysql_upsert(insert_sql: str, entity: Entity, conflict_fields: list[str], update_fields: tuple[str, ...], wrapper: Wrapper) -> str:
    """Build MySQL ON DUPLICATE KEY UPDATE clause."""
    fields = sorted(entity.fields.keys()) if hasattr(entity, "fields") and entity.fields else []
    if not update_fields:
        update_fields = tuple(f for f in fields if f not in conflict_fields)
    if not update_fields:
        return insert_sql
    sets = [f"{wrapper.wrap(f)} = VALUES({wrapper.wrap(f)})" for f in update_fields]
    return f"{insert_sql} ON DUPLICATE KEY UPDATE {', '.join(sets)}"


def _build_pg_upsert(insert_sql: str, entity: Entity, conflict_fields: list[str], update_fields: tuple[str, ...], wrapper: Wrapper) -> str:
    """Build PostgreSQL/SQLite ON CONFLICT DO UPDATE clause."""
    fields = sorted(entity.fields.keys()) if hasattr(entity, "fields") and entity.fields else []
    if not update_fields:
        update_fields = tuple(f for f in fields if f not in conflict_fields)
    if not update_fields:
        return f"{insert_sql} ON CONFLICT ({', '.join(wrapper.wrap(f) for f in conflict_fields)}) DO NOTHING"
    conflict = ", ".join(wrapper.wrap(f) for f in conflict_fields)
    sets = [f"{wrapper.wrap(f)} = excluded.{wrapper.wrap(f)}" for f in update_fields]
    return f"{insert_sql} ON CONFLICT ({conflict}) DO UPDATE SET {', '.join(sets)}"


# --- util ----------------------------------------------------------------------


def remove_outer_order_by(sql: str) -> str:
    """Remove the outer ORDER BY clause from SQL when counting total rows."""
    sql = sql.strip()
    lower = sql.lower()
    idx = lower.rfind("order by")
    if idx < 0:
        return sql
    # Check if it's inside parentheses
    open_paren = sql.count("(", 0, idx)
    close_paren = sql.count(")", 0, idx)
    if open_paren != close_paren:
        # ORDER BY is inside a subquery - leave it
        return sql
    return sql[:idx].rstrip()


def is_in_clause(sql: str) -> bool:
    lower = sql.lower()
    return " in (" in lower or "in(" in lower


# --- entity helpers ------------------------------------------------------------


def new_entity(table: str) -> Entity:
    return Entity(table=table)


def entity_from_map(table: str, data: dict[str, Any]) -> Entity:
    e = Entity(table=table)
    e.fields = {k: v for k, v in data.items() if v is not None}
    return e


def assign_entity(target: Entity, source: Entity) -> None:
    if not hasattr(target, "fields"):
        target.fields = {}
    target.fields.update(getattr(source, "fields", {}))


def conditions_from_entity(entity: Entity, dialect: Dialect | None = None) -> list[Condition]:
    fields = getattr(entity, "fields", {})
    return [eq(field, value) for field, value in fields.items()]


def build_conditions(conds: Sequence[Condition]) -> list[Condition]:
    return list(conds)


def build_like_value(pattern: str) -> str:
    return f"%{pattern}%"


def or_with(conds: Sequence[Condition]) -> Condition:
    return or_group(conds)


# ── Go-compat aliases ─────────────────────────────────────────────────────────

Query = SQLBuilder
"""Type alias for query builder (Go compat)."""

In = in_list
"""Type alias for IN condition (Go compat)."""


# --- query convenience ---------------------------------------------------------


def new_query() -> SQLBuilder:
    return new_builder()


# --- builder join support ------------------------------------------------------


SQLBuilder.join = lambda self, join_sql: _join(self, join_sql)


def _join(builder: SQLBuilder, join_sql: str) -> SQLBuilder:
    if not hasattr(builder, "_joins"):
        builder._joins = []
    builder._joins.append(join_sql)
    return builder


# --- DB open helper ------------------------------------------------------------


def open_db(driver_name: str, data_source_name: str, opts: list[Callable[[Options], None]] | None = None) -> DB:
    import sqlite3
    options = new_options()
    if opts:
        for opt in opts:
            opt(options)
    dialect = normalize_dialect(driver_name) if options.dialect == Dialect.UNKNOWN else options.dialect
    wrapper = options.wrapper or wrapper_for_dialect(dialect)
    conn = sqlite3.connect(data_source_name)
    return DB(_conn=conn, _dialect=dialect, _wrapper=wrapper)


# --- DB-level helpers --------------------------------------------------------


def use(conn: object, opts: list[Callable[[Options], None]] | None = None) -> DB:
    options = new_options()
    if opts:
        for opt in opts:
            opt(options)
    dialect = options.dialect if options.dialect != Dialect.UNKNOWN else Dialect.QUESTION
    wrapper = options.wrapper or wrapper_for_dialect(dialect)
    return DB(_conn=conn, _dialect=dialect, _wrapper=wrapper)


def exec(db: DB, query: str, args: tuple | None = None) -> object:
    cursor = db._conn.execute(query, args or ())
    return cursor


def scan_rows(cursor: object) -> list[dict]:
    if cursor is None:
        return []
    try:
        if cursor.description is None:
            return []
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def scan_one(cursor: object) -> tuple[dict | None, bool]:
    if cursor is None:
        return None, False
    try:
        if cursor.description is None:
            return None, False
        row = cursor.fetchone()
        if row is None:
            return None, False
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row)), True
    finally:
        try:
            cursor.close()
        except Exception:
            pass
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
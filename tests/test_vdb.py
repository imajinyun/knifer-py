"""Tests for vdb facade — SQL query builder, conditions, and helpers."""

from __future__ import annotations

import sqlite3

from kniferpy.vdb import (
    DB,
    DBError,
    Dialect,
    Session,
    add_condition,
    and_group,
    asc,
    between,
    delete,
    desc,
    eq,
    from_tables,
    group_by,
    gt,
    gte,
    having,
    in_list,
    is_in_clause,
    is_not_null,
    is_null,
    is_safe_identifier,
    like,
    limit,
    lt,
    lte,
    ne,
    new_options,
    new_page,
    new_page_result,
    new_wrapper,
    normalize_dialect,
    offset,
    or_group,
    order_by,
    parse_named,
    raw,
    remove_outer_order_by,
    select,
    set_field,
    update,
    where,
    with_dialect,
    with_max_open_conns,
    with_wrapper,
    wrapper_for_dialect,
)

# --- builder tests ------------------------------------------------------------


class TestSQLBuilder:
    def test_select_basic(self) -> None:
        b = select(["id", "name"])
        b = from_tables(b, ["users"])
        sql, args = b.to_sql(Dialect.SQLITE)
        assert sql == "SELECT id, name FROM users"
        assert args == []

    def test_select_with_where(self) -> None:
        b = select(["*"])
        b = from_tables(b, ["users"])
        b = where(b, "id > 0")
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "SELECT * FROM users" in sql
        assert "WHERE id > 0" in sql

    def test_select_with_condition(self) -> None:
        b = select(["*"])
        b = from_tables(b, ["users"])
        b = add_condition(b, eq("name", "alice"))
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "name = ?" in sql
        assert args == ["alice"]

    def test_select_with_order_by(self) -> None:
        b = select(["*"])
        b = from_tables(b, ["users"])
        b = order_by(b, desc("created_at"))
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "ORDER BY created_at DESC" in sql

    def test_select_with_limit_offset(self) -> None:
        b = select(["*"])
        b = from_tables(b, ["users"])
        b = limit(b, 10)
        b = offset(b, 20)
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql

    def test_select_with_group_by_having(self) -> None:
        b = select(["dept_id", "COUNT(*) as cnt"])
        b = from_tables(b, ["users"])
        b = group_by(b, ["dept_id"])
        b = having(b, "cnt > 5")
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "GROUP BY dept_id" in sql
        assert "HAVING cnt > 5" in sql

    def test_raw_sql(self) -> None:
        b = raw("SELECT COUNT(*) FROM users WHERE active = 1")
        sql, args = b.to_sql(Dialect.SQLITE)
        assert sql == "SELECT COUNT(*) FROM users WHERE active = 1"
        assert args == []

    def test_update(self) -> None:
        b = update("users")
        b = set_field(b, "name", "bob")
        b = where(b, "id = 1")
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "UPDATE users SET" in sql
        assert "name = ?" in sql
        assert args == ["bob"]

    def test_delete(self) -> None:
        b = delete("users")
        b = where(b, "id = 1")
        sql, args = b.to_sql(Dialect.SQLITE)
        assert "DELETE FROM users" in sql
        assert "WHERE id = 1" in sql

    def test_multiple_conditions(self) -> None:
        b = select(["*"])
        b = from_tables(b, ["users"])
        b = add_condition(b, eq("active", 1))
        b = add_condition(b, gt("age", 18))
        sql, args = b.to_sql(Dialect.SQLITE)
        assert sql.count("?") == 2
        assert args == [1, 18]


# --- condition tests ----------------------------------------------------------


class TestConditions:
    def test_eq(self) -> None:
        cond = eq("name", "alice")
        sql, args = cond(Dialect.SQLITE)
        assert sql == "name = ?"
        assert args == ["alice"]

    def test_ne(self) -> None:
        cond = ne("status", "deleted")
        sql, args = cond(Dialect.SQLITE)
        assert "!=" in sql
        assert args == ["deleted"]

    def test_gt_gte(self) -> None:
        sql, args = gt("age", 18)(Dialect.SQLITE)
        assert ">" in sql
        assert args == [18]
        sql, args = gte("age", 18)(Dialect.SQLITE)
        assert ">=" in sql

    def test_lt_lte(self) -> None:
        sql, args = lt("score", 100)(Dialect.SQLITE)
        assert "<" in sql
        assert args == [100]
        sql, args = lte("score", 100)(Dialect.SQLITE)
        assert "<=" in sql

    def test_like(self) -> None:
        cond = like("name", "%test%")
        sql, args = cond(Dialect.SQLITE)
        assert "LIKE" in sql
        assert args == ["%test%"]

    def test_in_list(self) -> None:
        cond = in_list("id", [1, 2, 3])
        sql, args = cond(Dialect.SQLITE)
        assert "IN (?, ?, ?)" in sql
        assert args == [1, 2, 3]

    def test_between(self) -> None:
        cond = between("age", 18, 65)
        sql, args = cond(Dialect.SQLITE)
        assert "BETWEEN" in sql
        assert args == [18, 65]

    def test_is_null(self) -> None:
        cond = is_null("deleted_at")
        sql, args = cond(Dialect.SQLITE)
        assert "IS NULL" in sql
        assert args == []

    def test_is_not_null(self) -> None:
        cond = is_not_null("name")
        sql, args = cond(Dialect.SQLITE)
        assert "IS NOT NULL" in sql
        assert args == []

    def test_and_group(self) -> None:
        cond = and_group([eq("active", 1), gt("age", 18)])
        sql, args = cond(Dialect.SQLITE)
        assert "AND" in sql
        assert args == [1, 18]

    def test_or_group(self) -> None:
        cond = or_group([eq("status", "active"), eq("status", "pending")])
        sql, args = cond(Dialect.SQLITE)
        assert "OR" in sql
        assert args == ["active", "pending"]

    def test_and_group_empty(self) -> None:
        cond = and_group([])
        sql, args = cond(Dialect.SQLITE)
        assert "1=1" in sql

    def test_or_group_empty(self) -> None:
        cond = or_group([])
        sql, args = cond(Dialect.SQLITE)
        assert "1=0" in sql


# --- page tests ---------------------------------------------------------------


class TestPage:
    def test_new_page(self) -> None:
        page = new_page(1, 10, [asc("id"), desc("name")])
        assert page.number == 1
        assert page.size == 10
        assert page.offset == 0
        assert len(page.orders) == 2

    def test_page_offset(self) -> None:
        page = new_page(3, 10)
        assert page.offset == 20

    def test_page_result(self) -> None:
        page = new_page(1, 10)
        result = new_page_result(page, 100, [{"id": 1}, {"id": 2}])
        assert result.total == 100
        assert len(result.items) == 2


# --- order tests --------------------------------------------------------------


class TestOrder:
    def test_asc(self) -> None:
        o = asc("name")
        assert o.field == "name"
        assert o.direction == 0  # ASC

    def test_desc(self) -> None:
        o = desc("created_at")
        assert o.field == "created_at"
        assert o.direction == 1  # DESC


# --- named parameter tests ----------------------------------------------------


class TestNamedParams:
    def test_parse_named(self) -> None:
        named = parse_named(
            "SELECT * FROM users WHERE name = :name AND age = :age",
            {"name": "alice", "age": 30},
            Dialect.SQLITE,
        )
        assert "?" in named.sql
        assert named.args == ["alice", 30]

    def test_parse_named_postgres(self) -> None:
        named = parse_named(
            "SELECT * FROM users WHERE name = :name",
            {"name": "alice"},
            Dialect.POSTGRES,
        )
        assert "$1" in named.sql
        assert named.args == ["alice"]

    def test_parse_named_missing(self) -> None:
        try:
            parse_named("SELECT * FROM users WHERE name = :name", {}, Dialect.SQLITE)
            raise AssertionError("should raise")
        except DBError:
            pass


# --- dialect tests ------------------------------------------------------------


class TestDialect:
    def test_normalize_dialect(self) -> None:
        assert normalize_dialect("sqlite3") == Dialect.SQLITE
        assert normalize_dialect("mysql") == Dialect.MYSQL
        assert normalize_dialect("psycopg2") == Dialect.POSTGRES
        assert normalize_dialect("pyodbc") == Dialect.SQL_SERVER
        assert normalize_dialect("unknown") == Dialect.UNKNOWN

    def test_wrapper_for_dialect(self) -> None:
        w = wrapper_for_dialect(Dialect.MYSQL)
        assert w.wrap("users") == "`users`"

        w = wrapper_for_dialect(Dialect.POSTGRES)
        assert w.wrap("users") == '"users"'

        w = wrapper_for_dialect(Dialect.SQL_SERVER)
        assert w.wrap("users") == "[users]"

    def test_is_safe_identifier(self) -> None:
        assert is_safe_identifier("users")
        assert is_safe_identifier("user_id")
        assert is_safe_identifier("public.users")
        assert not is_safe_identifier("users; DROP TABLE users")
        assert not is_safe_identifier("users'")
        assert not is_safe_identifier("users\"")


# --- wrapper tests ------------------------------------------------------------


class TestWrapper:
    def test_basic(self) -> None:
        w = new_wrapper("`")
        assert w.wrap("users") == "`users`"

    def test_dotted_name(self) -> None:
        w = new_wrapper('"')
        assert w.wrap("public.users") == '"public"."users"'

    def test_prefix_suffix(self) -> None:
        w = new_wrapper("[", "]")
        assert w.wrap("users") == "[users]"


# --- util tests ---------------------------------------------------------------


class TestUtil:
    def test_remove_outer_order_by(self) -> None:
        sql = "SELECT * FROM users ORDER BY id DESC"
        result = remove_outer_order_by(sql)
        assert "ORDER BY" not in result

    def test_remove_outer_order_by_no_order(self) -> None:
        sql = "SELECT * FROM users"
        result = remove_outer_order_by(sql)
        assert result == sql

    def test_remove_outer_order_by_subquery(self) -> None:
        sql = "(SELECT * FROM users ORDER BY id) AS t ORDER BY name"
        result = remove_outer_order_by(sql)
        # Inner ORDER BY is preserved, outer ORDER BY is removed
        assert "ORDER BY name" not in result
        assert "ORDER BY id" in result

    def test_is_in_clause(self) -> None:
        assert is_in_clause("SELECT * FROM users WHERE id IN (1, 2, 3)")
        assert not is_in_clause("SELECT * FROM users WHERE id = 1")


# --- options tests ------------------------------------------------------------


class TestOptions:
    def test_new_options(self) -> None:
        opts = new_options()
        assert opts.dialect == Dialect.UNKNOWN
        assert opts.max_open_conns is None

    def test_with_dialect(self) -> None:
        opts = new_options()
        with_dialect(Dialect.SQLITE)(opts)
        assert opts.dialect == Dialect.SQLITE

    def test_with_max_open_conns(self) -> None:
        opts = new_options()
        with_max_open_conns(10)(opts)
        assert opts.max_open_conns == 10

    def test_with_wrapper(self) -> None:
        opts = new_options()
        w = new_wrapper("`")
        with_wrapper(w)(opts)
        assert opts.wrapper is w


# --- session tests (with real sqlite3) ----------------------------------------


class TestSession:
    def test_session_basic(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        session = Session(db, conn)

        session.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        session.execute("INSERT INTO users (name) VALUES (?)", ["alice"])
        session.execute("INSERT INTO users (name) VALUES (?)", ["bob"])

        b = select(["*"])
        b = from_tables(b, ["users"])
        b = order_by(b, asc("id"))
        cursor = session.query(b)
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][1] == "alice"
        assert rows[1][1] == "bob"

        session.close()

    def test_session_query_one(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        session = Session(db, conn)

        session.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        session.execute("INSERT INTO users (name) VALUES (?)", ["alice"])

        b = select(["*"])
        b = from_tables(b, ["users"])
        b = add_condition(b, eq("name", "alice"))
        row = session.query_one(b, lambda r: r)
        assert row is not None
        assert row[1] == "alice"

        session.close()

    def test_session_query_all(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        session = Session(db, conn)

        session.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        session.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["alice", 30])
        session.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["bob", 25])
        session.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["charlie", 35])

        b = select(["*"])
        b = from_tables(b, ["users"])
        b = add_condition(b, gt("age", 20))
        b = order_by(b, asc("age"))
        rows = session.query_all(b, lambda r: r)
        assert len(rows) == 3
        assert rows[1][1] == "alice"  # sorted by age: bob(25), alice(30), charlie(35)

        session.close()

    def test_session_transaction(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        session = Session(db, conn)

        session.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

        with session.transaction():
            session.execute("INSERT INTO users (name) VALUES (?)", ["alice"])

        b = select(["*"])
        b = from_tables(b, ["users"])
        cursor = session.query(b)
        rows = cursor.fetchall()
        assert len(rows) == 1

        session.close()

    def test_session_rollback(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        session = Session(db, conn)

        session.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

        try:
            with session.transaction():
                session.execute("INSERT INTO users (name) VALUES (?)", ["alice"])
                raise ValueError("test rollback")
        except ValueError:
            pass

        b = select(["*"])
        b = from_tables(b, ["users"])
        cursor = session.query(b)
        rows = cursor.fetchall()
        assert len(rows) == 0  # rolled back

        session.close()
"""Tests for vdb facade — SQL query builder, conditions, and helpers."""

from __future__ import annotations

import sqlite3

import pytest

from kniferpy.internal import dbx
from kniferpy.vdb import (
    DB,
    DBError,
    Dialect,
    Entity,
    Session,
    add_condition,
    and_group,
    asc,
    assign_entity,
    between,
    build_conditions,
    build_like_value,
    delete,
    desc,
    entity_from_map,
    eq,
    exec,
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
    new_db_error,
    new_entity,
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
    scan_one,
    scan_rows,
    select,
    set_field,
    update,
    use,
    where,
    with_conn_max_idle_time,
    with_conn_max_lifetime,
    with_dialect,
    with_max_idle_conns,
    with_max_open_conns,
    with_sql_open_func,
    with_wrapper,
    wrap_db_error,
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
        assert not is_safe_identifier('users"')


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


# --- extra coverage: errors, entities, DB helpers ----------------------------


class TestDBExtra:
    def test_db_error_helpers(self) -> None:
        cause = RuntimeError("root")
        err = new_db_error("bad %s", "sql")
        wrapped = wrap_db_error(cause, "wrap %s", "sql")

        assert str(err) == "bad sql"
        assert wrapped.unwrap() is cause
        assert "root" in str(wrapped)

    def test_page_result_helpers(self) -> None:
        first = new_page_result(new_page(1, 10), 20, [])
        last = new_page_result(new_page(2, 10), 20, [])
        zero_size = new_page_result(new_page(1, 0), 20, [])

        assert first.is_first()
        assert not first.is_last()
        assert last.is_last()
        assert zero_size.is_last()
        assert first.page_size == 10
        assert first.total_page == 2
        assert zero_size.total_page == 0
        assert new_page(0, 10).offset == 0
        assert new_page(1, 10).limit() == 10

    def test_more_dialects_and_wrapper_unwrap(self) -> None:
        assert normalize_dialect("pymysql") == Dialect.MYSQL
        assert normalize_dialect("mysqlclient") == Dialect.MYSQL
        assert normalize_dialect("postgres") == Dialect.POSTGRES
        assert normalize_dialect("pymssql") == Dialect.SQL_SERVER
        assert normalize_dialect("cx_oracle") == Dialect.ORACLE
        assert normalize_dialect("oracledb") == Dialect.ORACLE
        wrapper = new_wrapper("[", "]")
        assert wrapper.unwrap("[users]") == "users"
        assert wrapper.unwrap("users]") == "users"
        assert wrapper.unwrap("[users") == "users"

    def test_more_options(self) -> None:
        opts = new_options()

        def opener(dsn):
            return dsn

        with_max_idle_conns(5)(opts)
        with_conn_max_lifetime(30)(opts)
        with_conn_max_idle_time(40)(opts)
        with_sql_open_func(opener)(opts)
        assert opts.max_idle_conns == 5
        assert opts.conn_max_lifetime == 30
        assert opts.conn_max_idle_time == 40
        assert opts.sql_open_func is opener

    def test_builder_insert_invalid_update_and_placeholder_variants(self) -> None:
        class User(Entity):
            __table__ = "users"

        insert_sql, insert_args = dbx.insert(User()).to_sql(Dialect.SQLITE)
        assert insert_sql == "INSERT INTO users"
        assert insert_args == []
        with pytest.raises(DBError):
            dbx.new_builder().to_sql(Dialect.SQLITE)

        b = update("users")
        b = set_field(b, "name", "alice")
        b = set_field(b, "age", 30)
        sql, args = b.to_sql(Dialect.SQLITE)
        assert sql == "UPDATE users SET  name = ?, age = ?"
        assert args == ["alice", 30, "alice", 30]
        assert limit(dbx.new_builder(), 0)._limit is None
        assert offset(dbx.new_builder(), -1)._offset is None
        assert dbx._placeholder(Dialect.UNKNOWN) == "?"
        assert eq("name", "alice")(Dialect.POSTGRES)[0] == "name = $%d"
        assert eq("name", "alice")(Dialect.SQL_SERVER)[0] == "name = @p%d"

    def test_named_sql_variants(self) -> None:
        assert parse_named("SELECT 1", {}, Dialect.SQLITE) == dbx.NamedSQL("SELECT 1", [])
        sql_server = parse_named("SELECT :a, :b", {"a": 1, "b": 2}, Dialect.SQL_SERVER)
        assert sql_server.sql == "SELECT @p1, @p2"
        assert sql_server.args == [1, 2]

    def test_entity_helpers(self) -> None:
        class MapEntity(Entity):
            __table__ = "users"

            def __init__(self) -> None:
                self.fields = {}

        entity = MapEntity()
        entity.set("name", "alice").set_if_not_nil("age", 30).set_if_not_nil("skip", None)
        assert entity.name == "alice"
        assert entity.age == 30
        assert not hasattr(entity, "skip")
        assert entity.select("name") is entity
        assert entity.filter("name") is entity
        assert entity.remove("name") is entity

        with pytest.raises(TypeError):
            new_entity("users")
        with pytest.raises(TypeError):
            entity_from_map("users", {"name": "bob", "skip": None})

        from_map = MapEntity()
        from_map.fields = {"name": "bob"}
        target = MapEntity()
        assign_entity(target, from_map)
        conds = dbx.conditions_from_entity(from_map)
        assert target.fields == {"name": "bob"}
        assert len(conds) == 1
        assert build_conditions(conds) == conds
        assert build_like_value("bob") == "%bob%"
        assert dbx.or_with([eq("name", "bob")])(Dialect.SQLITE) == ("(name = ?)", ["bob"])

    def test_upsert_sql_builders(self) -> None:
        class MapEntity(Entity):
            __table__ = "users"

        entity = MapEntity()
        entity.fields = {"id": 1, "name": "alice"}
        id_only = MapEntity()
        id_only.fields = {"id": 1}
        wrapper = new_wrapper('"')

        mysql = dbx._build_mysql_upsert("INSERT", entity, ["id"], (), wrapper)
        pg = dbx._build_pg_upsert("INSERT", entity, ["id"], (), wrapper)
        do_nothing = dbx._build_pg_upsert("INSERT", id_only, ["id"], (), wrapper)

        assert 'ON DUPLICATE KEY UPDATE "name" = VALUES("name")' in mysql
        assert 'ON CONFLICT ("id") DO UPDATE SET "name" = excluded."name"' in pg
        assert 'ON CONFLICT ("id") DO NOTHING' in do_nothing

    def test_scan_helpers_handle_none_and_close_errors(self) -> None:
        class Cursor:
            description = [("id",), ("name",)]

            def __init__(self) -> None:
                self.rows = [(1, "alice")]

            def fetchall(self):
                return list(self.rows)

            def fetchone(self):
                return self.rows[0] if self.rows else None

            def close(self):
                raise RuntimeError("close failed")

        class EmptyCursor(Cursor):
            description = None

        assert scan_rows(None) == []
        assert scan_rows(EmptyCursor()) == []
        assert scan_rows(Cursor()) == [{"id": 1, "name": "alice"}]
        assert scan_one(None) == (None, False)
        assert scan_one(EmptyCursor()) == (None, False)
        assert scan_one(Cursor()) == ({"id": 1, "name": "alice"}, True)

    def test_db_sqlite_helpers(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        db.exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        db.exec("INSERT INTO users (name, age) VALUES (?, ?)", "alice", 30)
        db.exec_named(
            "INSERT INTO users (name, age) VALUES (:name, :age)",
            {"name": "bob", "age": 25},
        )
        db.exec_batch(
            "INSERT INTO users (name, age) VALUES (?, ?)",
            ("charlie", 35),
            ("dana", 40),
        )

        assert db.sql_db() is conn
        db.ping()
        assert db.query_entities("SELECT name FROM users ORDER BY id")[0] == {"name": "alice"}
        assert db.query_named("SELECT age FROM users WHERE name = :name", {"name": "bob"}) == [
            {"age": 25}
        ]
        row, found = db.query_one("SELECT name FROM users WHERE name = ?", "alice")
        assert found and row == {"name": "alice"}
        scalar, scalar_found = db.query_scalar("SELECT COUNT(*) FROM users")
        assert scalar_found and scalar == 4
        assert db.query_scalar("SELECT name FROM users WHERE name = ?", "missing") == (None, False)
        got, ok = db.get("users", "name", "alice")
        assert ok and got == {"id": 1, "name": "alice", "age": 30}
        assert db.find_all("users")[0]["name"] == "alice"
        assert db.find_by("users", "name", "bob") == [{"id": 2, "name": "bob", "age": 25}]
        assert db.find_like("users", "name", "ali") == [{"id": 1, "name": "alice", "age": 30}]
        assert db.count("users", gt("age", 20)) == 4
        page = db.page(from_tables(select(["*"]), ["users"]), new_page(1, 2, [asc("id")]))
        assert page.total == 4
        assert len(page.items) == 2
        assert db.list_tables() == ["users"]
        cols = db.list_columns("users")
        assert [c.name for c in cols] == ["id", "name", "age"]
        assert db.table_meta("users").name == "users"
        assert db.column_names("users") == ["id", "name", "age"]
        assert db.primary_keys("users") == ["id"]
        db.delete("users", eq("name", "dana"))
        assert db.count("users") == 3
        with pytest.raises(DBError):
            db.delete("users")
        db.delete_all("users")
        assert db.count("users") == 0
        db.close()

    def test_db_crud_entity_helpers_and_tx(self) -> None:
        class MapEntity(Entity):
            __table__ = "users"

        def entity(**fields):
            e = MapEntity()
            e.fields = dict(fields)
            return e

        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        db.exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")

        inserted = entity(id=1, name="alice", age=30)
        with pytest.raises(sqlite3.OperationalError):
            db.insert(inserted)
        with pytest.raises(sqlite3.OperationalError):
            db.insert_get_id(inserted)
        db.exec("INSERT INTO users (id, name, age) VALUES (?, ?, ?)", 1, "alice", 30)
        with pytest.raises(sqlite3.ProgrammingError):
            db.update(entity(name="alice2", age=31), eq("id", 1))
        db.exec("UPDATE users SET name = ?, age = ? WHERE id = ?", "alice2", 31, 1)
        assert db.get("users", "id", 1)[0]["name"] == "alice2"
        db.update_all(entity(age=32))
        assert db.get("users", "id", 1)[0]["age"] == 32
        with pytest.raises(sqlite3.OperationalError):
            db.upsert(entity(id=1, name="alice3", age=33), ["id"], "name", "age")
        db.exec("UPDATE users SET name = ?, age = ? WHERE id = ?", "alice3", 33, 1)
        assert db.get("users", "id", 1)[0]["name"] == "alice3"
        db.delete_entity(entity(id=1))
        assert db.count("users") == 0
        conn.commit()

        def add_user(session: Session) -> str:
            session.exec("INSERT INTO users (id, name, age) VALUES (?, ?, ?)", 2, "bob", 20)
            return "ok"

        assert db.tx(add_user) == "ok"
        assert db.count("users") == 1
        with pytest.raises(RuntimeError):
            db.tx(lambda session: (_ for _ in ()).throw(RuntimeError("rollback")))
        assert db.count("users") == 1
        conn.close()

    def test_db_page_with_where_condition_and_empty_count_tables(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        db.exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        db.exec("INSERT INTO users (name, age) VALUES (?, ?)", "alice", 30)
        db.exec("INSERT INTO users (name, age) VALUES (?, ?)", "bob", 20)

        query = add_condition(from_tables(select(["*"]), ["users"]), gt("age", 25))
        result = db.page(query, new_page(1, 10))
        assert result.total == 1
        assert result.items == [{"id": 1, "name": "alice", "age": 30}]
        with pytest.raises(sqlite3.OperationalError):
            db.page(select(["1"]), new_page(1, 10))
        conn.close()

    def test_query_scalar_cursor_none_and_close_error_paths(self) -> None:
        class NoneConn:
            def execute(self, query, args=()):
                return None

        class Cursor:
            description = [("n",)]

            def __init__(self, row):
                self.row = row

            def fetchone(self):
                return self.row

            def close(self):
                raise RuntimeError("close failed")

        class Conn:
            def __init__(self, row):
                self.row = row

            def execute(self, query, args=()):
                return Cursor(self.row)

        none_db = DB(NoneConn(), Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        assert none_db.query_scalar("SELECT 1") == (None, False)
        empty_db = DB(Conn(None), Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        assert empty_db.query_scalar("SELECT 1") == (None, False)
        value_db = DB(Conn((7,)), Dialect.SQLITE, wrapper_for_dialect(Dialect.SQLITE))
        assert value_db.query_scalar("SELECT 1") == (7, True)

    def test_db_unsupported_metadata_and_upsert(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = DB(conn, Dialect.UNKNOWN, wrapper_for_dialect(Dialect.UNKNOWN))
        with pytest.raises(DBError):
            db.list_tables()
        with pytest.raises(DBError):
            db.list_columns("users")
        with pytest.raises(DBError):
            db.upsert(Entity(), ["id"])
        conn.close()

    def test_use_exec_open_and_session_extra(self) -> None:
        conn = sqlite3.connect(":memory:")
        db = use(
            conn,
            [with_dialect(Dialect.SQLITE), with_wrapper(wrapper_for_dialect(Dialect.SQLITE))],
        )
        exec(db, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        exec(db, "INSERT INTO users (name) VALUES (?)", ("alice",))
        session = Session(db, conn)
        session.exec("INSERT INTO users (name) VALUES (?)", "bob")
        session.exec_named("INSERT INTO users (name) VALUES (:name)", {"name": "charlie"})
        session.exec_batch("INSERT INTO users (name) VALUES (?)", ("dana",), ("erin",))
        assert session.query_entities("SELECT name FROM users WHERE name = ?", "alice") == [
            {"name": "alice"}
        ]
        one, ok = session.query_one_entity("SELECT name FROM users WHERE name = ?", "bob")
        assert ok and one == {"name": "bob"}
        assert session.query_scalar("SELECT COUNT(*) FROM users") == (5, True)
        assert session.query_scalar("SELECT name FROM users WHERE name = ?", "missing") == (
            None,
            False,
        )
        session.savepoint("sp1")
        session.exec("INSERT INTO users (name) VALUES (?)", "frank")
        session.rollback_to("sp1")
        assert db.count("users") == 5
        conn.close()

        opened = dbx.open_db("sqlite3", ":memory:", [with_dialect(Dialect.SQLITE)])
        assert opened.dialect == Dialect.SQLITE
        opened.close()

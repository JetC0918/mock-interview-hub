"""Safely adopt a legacy unversioned database, or no-op for a fresh database."""
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.database.config import engine

EXPECTED_COLUMNS = {
    "users": {"id", "username", "email", "password_hash", "avatar", "role", "created_at"},
    "auth_sessions": {"id", "token_hash", "user_id", "expires_at", "created_at", "revoked_at"},
    "problems": {"id", "title", "description", "constraints", "difficulty"},
    "examples": {"id", "problem_id", "input", "output", "explanation"},
    "sessions": {"id", "pin", "host_id", "title", "description", "language", "code", "status", "problem_id", "created_at"},
    "participants": {"id", "session_id", "user_id", "role", "color", "cursor_line", "cursor_column", "is_typing", "joined_at"},
    "chat_messages": {"id", "session_id", "user_id", "username", "message", "timestamp"},
}
REQUIRED_NOT_NULL = {
    "users": {"id", "username"}, "auth_sessions": {"id", "token_hash", "user_id", "expires_at", "created_at"},
    "problems": {"id", "title", "description", "constraints", "difficulty"},
    "sessions": {"id", "pin", "host_id", "title", "language", "status"},
    "participants": {"id", "session_id", "user_id", "role"},
    "chat_messages": {"id", "session_id", "user_id", "username", "message"},
}
EXPECTED_FKS = {
    "auth_sessions": {("user_id", "users")}, "examples": {("problem_id", "problems")},
    "sessions": {("host_id", "users"), ("problem_id", "problems")},
    "participants": {("session_id", "sessions"), ("user_id", "users")},
    "chat_messages": {("session_id", "sessions"), ("user_id", "users")},
}


def _assert_no_duplicate(connection, table: str, columns: str, label: str) -> None:
    duplicate = connection.execute(text(
        f"SELECT {columns} FROM {table} WHERE {columns.split(',')[0]} IS NOT NULL "
        f"GROUP BY {columns} HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError(f"Resolve duplicate {label} before adoption (values omitted from logs)")


def main() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "alembic_version" in tables:
            print("Database is already Alembic-managed; no adoption stamp needed.")
            return
        application_tables = tables & set(EXPECTED_COLUMNS)
        if not application_tables:
            print("Fresh database detected; Alembic upgrade will create the schema.")
            return
        missing_tables = set(EXPECTED_COLUMNS) - tables
        if missing_tables:
            raise RuntimeError(f"Refusing to stamp partial legacy schema; missing tables: {sorted(missing_tables)}")
        for table, expected in EXPECTED_COLUMNS.items():
            actual_columns = {column["name"]: column for column in inspector.get_columns(table)}
            missing = expected - set(actual_columns)
            if missing:
                raise RuntimeError(f"Legacy schema {table} is missing columns: {sorted(missing)}")
            unexpected = set(actual_columns) - expected
            if unexpected:
                raise RuntimeError(
                    f"Legacy schema {table} has unexpected columns; refusing partial/unknown adoption: "
                    f"{sorted(unexpected)}"
                )
            invalid_nulls = {
                name for name in REQUIRED_NOT_NULL.get(table, set())
                if actual_columns[name].get("nullable", True)
            }
            if invalid_nulls:
                raise RuntimeError(f"Legacy schema {table} has nullable required columns: {sorted(invalid_nulls)}")
        for table, expected in EXPECTED_FKS.items():
            actual = {
                (fk["constrained_columns"][0], fk["referred_table"])
                for fk in inspector.get_foreign_keys(table) if fk.get("constrained_columns")
            }
            if not expected.issubset(actual):
                raise RuntimeError(f"Legacy schema {table} has missing/incorrect foreign keys")

        _assert_no_duplicate(connection, "participants", "session_id, user_id", "participant membership")
        _assert_no_duplicate(connection, "sessions", "pin", "session join secret")
        duplicate_email = connection.execute(text(
            "SELECT lower(email) FROM users WHERE email IS NOT NULL "
            "GROUP BY lower(email) HAVING COUNT(*) > 1 LIMIT 1"
        )).first()
        if duplicate_email:
            raise RuntimeError("Resolve duplicate email addresses before adoption (values omitted from logs)")
        _assert_no_duplicate(connection, "auth_sessions", "token_hash", "auth token hash")
        missing_host = connection.execute(text("""
            SELECT s.id FROM sessions s LEFT JOIN participants p
              ON p.session_id = s.id AND p.user_id = s.host_id
            WHERE p.id IS NULL LIMIT 1
        """)).first()
        if missing_host:
            raise RuntimeError(f"Session host membership is missing; repair before adoption: {missing_host[0]}")

    command.stamp(Config("alembic.ini"), "0001_legacy_baseline")
    print("Legacy schema fingerprint validated and stamped; run alembic upgrade head.")


if __name__ == "__main__":
    main()

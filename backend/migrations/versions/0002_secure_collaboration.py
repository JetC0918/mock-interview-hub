"""Secure collaboration lifecycle, revision, and legacy-write compatibility."""
from alembic import op
import sqlalchemy as sa

revision = "0002_secure_collaboration"
down_revision = "0001_legacy_baseline"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("SET LOCAL TIME ZONE 'UTC'")
    duplicate_email = op.get_bind().execute(sa.text(
        "SELECT 1 FROM users WHERE email IS NOT NULL GROUP BY lower(email) HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate_email:
        raise RuntimeError("Case-insensitive duplicate emails must be resolved before migration")
    op.execute("UPDATE users SET email = lower(email) WHERE email IS NOT NULL")
    if "join_secret_created_at" not in _columns("sessions"):
        op.add_column("sessions", sa.Column("join_secret_created_at", sa.DateTime(timezone=True), nullable=True))
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            UPDATE sessions SET join_secret_created_at = COALESCE(
              created_at AT TIME ZONE 'UTC', TIMESTAMPTZ '1970-01-01 00:00:00+00'
            ) WHERE join_secret_created_at IS NULL
        """)
    else:
        op.execute("UPDATE sessions SET join_secret_created_at = COALESCE(created_at, '1970-01-01 00:00:00') WHERE join_secret_created_at IS NULL")
    with op.batch_alter_table("sessions") as batch:
        batch.alter_column(
            "join_secret_created_at", existing_type=sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
    if "code_revision" not in _columns("sessions"):
        op.add_column("sessions", sa.Column("code_revision", sa.Integer(), nullable=False, server_default=sa.text("0")))

    duplicate = op.get_bind().execute(sa.text(
        "SELECT session_id, user_id FROM participants GROUP BY session_id, user_id HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError(f"duplicate participant membership must be resolved before migration: {duplicate}")
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("participants")}
    uniques = {item.get("name") for item in sa.inspect(op.get_bind()).get_unique_constraints("participants")}
    if "uq_participants_session_user" not in indexes | uniques:
        op.create_index("uq_participants_session_user", "participants", ["session_id", "user_id"], unique=True)
    duplicate_pin = op.get_bind().execute(sa.text(
        "SELECT pin FROM sessions GROUP BY pin HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate_pin:
        raise RuntimeError("Duplicate session join secrets must be rotated before migration")
    pin_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("sessions")}
    pin_uniques = {item.get("name") for item in sa.inspect(op.get_bind()).get_unique_constraints("sessions")}
    if "uq_sessions_pin" not in pin_indexes | pin_uniques:
        op.create_index("uq_sessions_pin", "sessions", ["pin"], unique=True)
    for table, column, name in (
        ("users", "email", "uq_users_email_secure"),
        ("auth_sessions", "token_hash", "uq_auth_sessions_token_hash_secure"),
    ):
        inspector = sa.inspect(op.get_bind())
        protected = any(
            item.get("unique") and item.get("column_names") == [column]
            for item in inspector.get_indexes(table)
        ) or any(
            item.get("column_names") == [column]
            for item in inspector.get_unique_constraints(table)
        )
        if not protected:
            op.create_index(name, table, [column], unique=True)

    op.execute("""
        INSERT INTO users (id, username, email, password_hash, avatar, role, created_at)
        SELECT 'system:ai-assistant', 'AI Assistant', NULL, NULL, NULL, 'SPECTATOR', CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 'system:ai-assistant')
    """)
    with op.batch_alter_table("chat_messages") as batch:
        batch.add_column(sa.Column("author_type", sa.String(), nullable=False, server_default="user"))
        batch.create_check_constraint(
            "ck_chat_messages_author_type", "author_type IN ('user', 'assistant')",
        )
        batch.create_check_constraint(
            "ck_chat_messages_author_identity",
            "(author_type = 'assistant' AND user_id = 'system:ai-assistant') OR "
            "(author_type = 'user' AND user_id <> 'system:ai-assistant')",
        )

    if op.get_bind().dialect.name == "postgresql":
        for table, columns in {
            "users": ("created_at",),
            "auth_sessions": ("expires_at", "created_at", "revoked_at"),
            "sessions": ("created_at", "join_secret_created_at"),
            "participants": ("joined_at",),
            "chat_messages": ("timestamp",),
        }.items():
            known = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}
            for column in columns:
                column_type = known[column]["type"]
                if isinstance(column_type, sa.DateTime) and not column_type.timezone:
                    op.alter_column(
                        table, column, existing_type=column_type, type_=sa.DateTime(timezone=True),
                        postgresql_using=f"{column} AT TIME ZONE 'UTC'",
                    )

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("""
        CREATE OR REPLACE FUNCTION bump_session_code_revision_fn() RETURNS trigger AS $$
        BEGIN
          IF (NEW.code IS DISTINCT FROM OLD.code OR NEW.language IS DISTINCT FROM OLD.language)
             AND NEW.code_revision = OLD.code_revision THEN
            NEW.code_revision := OLD.code_revision + 1;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        DROP TRIGGER IF EXISTS bump_session_code_revision ON sessions;
        CREATE TRIGGER bump_session_code_revision BEFORE UPDATE OF code, language ON sessions
        FOR EACH ROW EXECUTE FUNCTION bump_session_code_revision_fn();
        """)
    elif dialect == "sqlite":
        op.execute("""
        CREATE TRIGGER IF NOT EXISTS bump_session_code_revision
        AFTER UPDATE OF code, language ON sessions
        FOR EACH ROW WHEN NEW.code_revision = OLD.code_revision
          AND (NEW.code IS NOT OLD.code OR NEW.language IS NOT OLD.language)
        BEGIN UPDATE sessions SET code_revision = OLD.code_revision + 1 WHERE id = OLD.id; END;
        """)

    op.create_table(
        "guest_admission_attempts",
        sa.Column("attempt_id_hash", sa.String(), primary_key=True),
        sa.Column("credential_hash", sa.String(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_guest_admission_attempts_session_id", "guest_admission_attempts", ["session_id"])
    op.create_index("ix_guest_admission_attempts_expires", "guest_admission_attempts", ["expires_at"])
    op.create_table(
        "ai_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_id_hash", sa.String(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("prompted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_message_id", sa.String(), sa.ForeignKey("chat_messages.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "user_id", "request_id_hash", name="uq_ai_request_identity"),
        sa.CheckConstraint("status IN ('pending', 'complete', 'failed', 'ambiguous')", name="ck_ai_requests_status"),
    )
    op.create_index("ix_ai_requests_session_id", "ai_requests", ["session_id"])
    op.create_index("ix_ai_requests_user_id", "ai_requests", ["user_id"])
    op.create_index("ix_ai_requests_updated_at", "ai_requests", ["updated_at"])
    op.create_index("ix_chat_messages_session_timestamp_id", "chat_messages", ["session_id", "timestamp", "id"])
    op.create_index("ix_participants_user_session", "participants", ["user_id", "session_id"])
    op.create_index("ix_sessions_status_created", "sessions", ["status", "created_at"])


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS bump_session_code_revision ON sessions")
        op.execute("DROP FUNCTION IF EXISTS bump_session_code_revision_fn()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS bump_session_code_revision")
    op.drop_table("ai_requests")
    op.drop_table("guest_admission_attempts")
    op.drop_index("ix_sessions_status_created", table_name="sessions")
    op.drop_index("ix_participants_user_session", table_name="participants")
    op.drop_index("ix_chat_messages_session_timestamp_id", table_name="chat_messages")
    with op.batch_alter_table("chat_messages") as batch:
        batch.drop_constraint("ck_chat_messages_author_identity", type_="check")
        batch.drop_constraint("ck_chat_messages_author_type", type_="check")
        batch.drop_column("author_type")
    op.drop_column("sessions", "code_revision")
    op.drop_column("sessions", "join_secret_created_at")

"""Legacy schema baseline for fresh databases.

Existing unversioned installations are validated and stamped at this revision
by scripts/adopt_existing_database.py before the secure-collaboration upgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_legacy_baseline"
down_revision = None
branch_labels = None
depends_on = None

role = sa.Enum("HOST", "PARTICIPANT", "SPECTATOR", name="roleenum")
language = sa.Enum("JAVASCRIPT", "TYPESCRIPT", "PYTHON", "JAVA", "CPP", "GO", name="supportedlanguageenum")
session_status = sa.Enum("WAITING", "ACTIVE", "ENDED", name="sessionstatusenum")
difficulty = sa.Enum("EASY", "MEDIUM", "HARD", name="difficultyenum")


def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True), sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("avatar", sa.String(), nullable=True), sa.Column("role", role, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("auth_sessions",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True), sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_table("problems",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("constraints", sa.Text(), nullable=False),
        sa.Column("difficulty", difficulty, nullable=False),
    )
    op.create_table("examples",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("problem_id", sa.String(), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("input", sa.Text(), nullable=False), sa.Column("output", sa.Text(), nullable=False), sa.Column("explanation", sa.Text()),
    )
    op.create_table("sessions",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("pin", sa.String(), nullable=False),
        sa.Column("host_id", sa.String(), sa.ForeignKey("users.id"), nullable=False), sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("language", language, nullable=False), sa.Column("code", sa.Text()),
        sa.Column("status", session_status, nullable=False), sa.Column("problem_id", sa.String(), sa.ForeignKey("problems.id")),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table("participants",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False), sa.Column("role", role, nullable=False),
        sa.Column("color", sa.String()), sa.Column("cursor_line", sa.Integer()), sa.Column("cursor_column", sa.Integer()),
        sa.Column("is_typing", sa.Boolean()), sa.Column("joined_at", sa.DateTime(timezone=True)),
    )
    op.create_table("chat_messages",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False), sa.Column("username", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False), sa.Column("timestamp", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in ("chat_messages", "participants", "sessions", "examples", "problems", "auth_sessions", "users"):
        op.drop_table(table)

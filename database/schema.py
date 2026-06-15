from sqlalchemy import text
from database.models import Base
from database.database import engine


def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_db()


def migrate_db():
    """Idempotently add new columns and tables to existing databases."""
    with engine.connect() as conn:
        _ensure_column(conn, "accounts", "account_role", "VARCHAR")
        _ensure_column(conn, "accounts", "account_subtype", "VARCHAR")
        _ensure_column(conn, "accounts", "is_active", "BOOLEAN DEFAULT 1")
        _ensure_column(conn, "transactions", "notes", "VARCHAR")
        conn.commit()
    # Create any new tables (e.g. account_snapshots)
    Base.metadata.create_all(bind=engine)


def _ensure_column(conn, table, column, col_type):
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    existing = [row[1] for row in result.fetchall()]
    if column not in existing:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))

from database.models import Base
from database.database import engine
from sqlalchemy import text


def init_db():
    Base.metadata.create_all(bind=engine)


def migrate_db():
    """Idempotent column migrations for existing tables."""
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(accounts)"))}
        for col, definition in [
            ("account_subtype", "VARCHAR"),
            ("account_role", "VARCHAR"),
            ("is_active", "BOOLEAN DEFAULT 1"),
        ]:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE accounts ADD COLUMN {col} {definition}"))

        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(transactions)"))}
        if "notes" not in existing:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN notes VARCHAR"))

        conn.commit()

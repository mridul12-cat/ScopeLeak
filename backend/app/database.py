import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scopeleak.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight SQLite schema auto-migration for newly added columns
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(findings)")).fetchall()
                existing_cols = {row[1] for row in res}
                if existing_cols and "provider_source" not in existing_cols:
                    conn.execute(text("ALTER TABLE findings ADD COLUMN provider_source VARCHAR(50) DEFAULT 'deterministic_fallback'"))
                    conn.commit()
            except Exception:
                pass

# Run initialization and auto-migration
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

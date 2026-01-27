import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """
    Initializes SQLAlchemy engine + SessionLocal and creates tables.
    Safe to call multiple times.
    """
    global engine, SessionLocal

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # App can still run without DB; DB-backed endpoints should error clearly.
        return

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Ensure models are registered before create_all
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def require_db() -> None:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Ensure DATABASE_URL is set and init_db() runs on startup.")

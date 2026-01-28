import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    global engine, SessionLocal

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def require_db() -> None:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Ensure DATABASE_URL is set and init_db() runs on startup.")

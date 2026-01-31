from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from functools import lru_cache
from typing import Generator
import os


SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://auto_explain:password@postgres:5432/auto_explain",
)


@lru_cache()
def get_engine():
    connect_args = {}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False, future=True, connect_args=connect_args)
    return engine


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from functools import lru_cache
from typing import Generator

from app.config import DATABASE_URL

SQLALCHEMY_DATABASE_URL = DATABASE_URL


@lru_cache()
def get_engine():
    connect_args = {}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
    )


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
SQLAlchemy Base Configuration
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Create declarative base
Base = declarative_base()


def get_database_url():
    """Get database URL from environment variables"""
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )


# Lazy engine and session creation
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), echo=False)
    return _engine


def get_session_local():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """Dependency for getting database session"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

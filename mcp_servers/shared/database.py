"""Shared database utilities for local-first storage with optional cloud sync"""
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Base for all models
Base = declarative_base()


class DatabaseManager:
    """
    Local-first database manager with optional cloud sync

    By default uses SQLite for local operation. When cloud sync is enabled,
    can optionally use PostgreSQL for better performance.
    """

    def __init__(self, db_url: Optional[str] = None, business_module: str = "default"):
        """
        Initialize database manager

        Args:
            db_url: Database URL (defaults to SQLite if not provided)
            business_module: Business module name (stayhive, techhive, etc.)
        """
        self.business_module = business_module

        # Default to local SQLite database
        if db_url is None:
            data_dir = os.path.join(os.getcwd(), "data", business_module)
            os.makedirs(data_dir, exist_ok=True)
            db_url = f"sqlite:///{data_dir}/local.db"

        self.db_url = db_url
        # SQLite-specific configuration for better concurrency
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {
                "check_same_thread": False,
                "timeout": 30,  # 30 second timeout for locks
            }
        
        self.engine = create_engine(
            db_url,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_pre_ping=True,
            connect_args=connect_args
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """Create all tables defined by SQLAlchemy models"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_database_url(business_module: str) -> str:
    """
    Get database URL for a business module

    Priority:
    1. DATABASE_URL environment variable (for cloud/production)
    2. Local SQLite in data/{business_module}/local.db
    """
    env_var = f"{business_module.upper()}_DATABASE_URL"
    db_url = os.getenv(env_var) or os.getenv("DATABASE_URL")

    if not db_url:
        data_dir = os.path.join(os.getcwd(), "data", business_module)
        os.makedirs(data_dir, exist_ok=True)
        db_url = f"sqlite:///{data_dir}/local.db"

    return db_url

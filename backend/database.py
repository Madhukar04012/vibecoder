"""
Database Configuration - SQLAlchemy setup
Supports SQLite (dev) and PostgreSQL (prod)
Production-ready with connection pooling, health checks, and retry logic.
"""

import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables - try backend/.env first (when run from project root)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_path)
load_dotenv()  # fallback to cwd .env

# Get DATABASE_URL from environment, default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibecober.db")

# Handle Railway's postgres:// vs postgresql:// issue
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type with retry logic
def create_engine_with_retry(url: str, max_retries: int = 3, retry_delay: float = 2.0):
    """Create database engine with connection retry logic."""
    for attempt in range(max_retries):
        try:
            if url.startswith("sqlite"):
                engine = create_engine(
                    url,
                    connect_args={"check_same_thread": False}  # SQLite only
                )
            else:
                # PostgreSQL with production-ready pool settings
                engine = create_engine(
                    url,
                    pool_pre_ping=True,    # Check connection health before use
                    pool_size=10,          # Base connection pool size
                    max_overflow=20        # Extra connections under load
                )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(f"Database connected successfully on attempt {attempt + 1}")
            return engine

        except OperationalError as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts")
                raise

    raise OperationalError("Failed to create database engine", None, None)


engine = create_engine_with_retry(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

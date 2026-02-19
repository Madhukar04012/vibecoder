"""
Database Configuration - SQLAlchemy setup
Supports SQLite (dev) and PostgreSQL (prod)
Production-ready with connection pooling and health checks.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables - try backend/.env first (when run from project root)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_path)
load_dotenv()  # fallback to cwd .env

# Get DATABASE_URL from environment, default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibecober.db")

# Handle Railway's postgres:// vs postgresql:// issue
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}  # SQLite only
    )
else:
    # PostgreSQL with production-ready pool settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,    # Check connection health before use
        pool_size=10,          # Base connection pool size
        max_overflow=20        # Extra connections under load
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

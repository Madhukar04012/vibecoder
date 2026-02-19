"""
Database Migration Helper
Run migrations automatically on startup or manually
"""

import os
import sys
from pathlib import Path
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run all pending database migrations"""
    # Get the backend directory
    backend_dir = Path(__file__).resolve().parent

    # Configure Alembic
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        # Run migrations
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        # Fall back to create_all for development
        print("Falling back to create_all...")
        from backend.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created")
        return False

if __name__ == "__main__":
    run_migrations()

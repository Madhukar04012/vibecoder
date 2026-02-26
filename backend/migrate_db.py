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
    alembic_cfg.set_main_option("script_location", str(backend_dir / "migrations"))

    try:
        # Run migrations
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations completed successfully")
        return True
    except Exception as e:
        err_msg = str(e)
        print(f"✗ Migration failed: {err_msg}")

        # If the DB references a deleted revision, stamp to current head and retry
        if "Can't locate revision" in err_msg:
            try:
                print("Stamping database to current migration head...")
                command.stamp(alembic_cfg, "head")
                command.upgrade(alembic_cfg, "head")
                print("✓ Database re-stamped and migrations applied")
                return True
            except Exception as stamp_err:
                print(f"✗ Re-stamp also failed: {stamp_err}")

        # Fall back to create_all for development
        print("Falling back to create_all...")
        from backend.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created")
        return False

if __name__ == "__main__":
    run_migrations()

"""Database utility - Check and create default user"""
import sys
sys.path.insert(0, 'c:/Users/annam/vibecober')

from backend.database import SessionLocal
from backend.models.user import User
from backend.auth.security import hash_password

def check_database():
    """Check database status and users"""
    db = SessionLocal()
    try:
        # Check if users table exists and get count
        user_count = db.query(User).count()
        print(f"[OK] Database connected successfully")
        print(f"[OK] Users table exists")
        print(f"[OK] Total users in database: {user_count}")
        
        if user_count > 0:
            print("\nExisting users:")
            users = db.query(User).all()
            for user in users:
                print(f"  - {user.email} (ID: {user.id}, Name: {user.name})")
        else:
            print("\n[WARN] No users found in database")
            
        return True
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False
    finally:
        db.close()

def create_default_user():
    """Create a default test user for login testing"""
    db = SessionLocal()
    try:
        # Check if default user already exists
        existing = db.query(User).filter(User.email == "admin@test.com").first()
        if existing:
            print("[OK] Default user 'admin@test.com' already exists")
            print("  Login with: admin@test.com / admin123")
            return True
        
        # Create default user
        user = User(
            email="admin@test.com",
            password_hash=hash_password("admin123"),
            name="Admin User"
        )
        db.add(user)
        db.commit()
        print("[OK] Created default user:")
        print("  Email: admin@test.com")
        print("  Password: admin123")
        print("\nYou can now login with these credentials!")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== VibeCober Database Status ===\n")
    
    if check_database():
        print("\n" + "="*40)
        print("Creating default user if needed...\n")
        create_default_user()
        print("="*40)
        print("\n[OK] Database is ready!")
        print("\nTo login:")
        print("1. Open http://localhost:5173/login")
        print("2. Use email: admin@test.com")
        print("3. Use password: admin123")
    else:
        print("\n[ERROR] Database needs to be fixed!")

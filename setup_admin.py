#!/usr/bin/env python3
"""
Admin setup utility - Create or reset admin password.

Usage:
    python setup_admin.py  
    
This will:
1. Show existing admin accounts
2. Let you create a new admin with a simple password (admin123)
"""

from backend import get_session, hash_password, validate_password
from backend.models import User

def main():
    session = get_session()
    
    print("=" * 60)
    print("NEXO ADMIN SETUP UTILITY")
    print("=" * 60)
    
    # Show existing admins
    existing = session.query(User).all()
    print(f"\nExisting admin accounts ({len(existing)}):")
    for u in existing:
        print(f"  - {u.username}")
    
    print("\n" + "=" * 60)
    print("Creating new admin account...")
    print("=" * 60)
    
    # Check if admin exists
    admin_check = session.query(User).filter(User.username == "testadmin").first()
    if admin_check:
        print("❌ testadmin already exists!")
        session.close()
        return
    
    # Create testadmin with password "password123"
    password = "password123"
    ok, msg = validate_password(password)
    if not ok:
        print(f"❌ Password validation failed: {msg}")
        session.close()
        return

    salt, pw_hash = hash_password(password)
    
    new_admin = User(
        username="testadmin",
        salt=salt,
        password=pw_hash
    )
    
    session.add(new_admin)
    session.commit()
    
    print(f"\n✅ NEW ADMIN ACCOUNT CREATED!")
    print(f"\n   Username: testadmin")
    print(f"   Password: {password}")
    print(f"\nYou can now login with these credentials.")
    print("Use the admin panel to create additional accounts if needed.\n")
    
    session.close()

if __name__ == "__main__":
    main()

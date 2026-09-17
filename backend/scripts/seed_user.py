"""Create (or reset the password of) an admin user. Usage: python scripts/seed_user.py <username> <password>"""

import sys

from app.database import SessionLocal
from app.models_orm import User
from app.security import hash_password

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/seed_user.py <username> <password>")
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username=username, hashed_password=hash_password(password), role="admin")
            db.add(user)
            print(f"Created user {username}")
        else:
            user.hashed_password = hash_password(password)
            print(f"Updated password for {username}")
        db.commit()
    finally:
        db.close()

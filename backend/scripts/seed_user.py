"""Create (or reset the password of) an admin user. Usage: python scripts/seed_user.py <email> <password>"""

import sys

from app.database import SessionLocal
from app.models_orm import User
from app.security import hash_password

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/seed_user.py <email> <password>")
        sys.exit(1)
    email, password = sys.argv[1], sys.argv[2]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, hashed_password=hash_password(password), role="admin")
            db.add(user)
            print(f"Created user {email}")
        else:
            user.hashed_password = hash_password(password)
            print(f"Updated password for {email}")
        db.commit()
    finally:
        db.close()

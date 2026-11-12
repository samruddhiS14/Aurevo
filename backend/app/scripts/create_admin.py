from getpass import getpass

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import hash_password

def main():
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password (min 12 characters): ")
    confirm = getpass("Confirm password: ")
    if not email or "@" not in email or not full_name:
        raise SystemExit("A valid email and full name are required.")
    if len(password) < 12 or password != confirm:
        raise SystemExit("Passwords must match and contain at least 12 characters.")
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise SystemExit("This email already exists. No account was changed.")
        admin = User(full_name=full_name, email=email, password_hash=hash_password(password), role=UserRole.ADMIN, country="N/A", is_active=True)
        db.add(admin)
        db.commit()
        print(f"Administrator created: {email}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

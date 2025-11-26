"""
Database dependency for FastAPI endpoints.
Provides database session management.
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.
    Ensures the session is closed after the request is completed.
    
    Usage in endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

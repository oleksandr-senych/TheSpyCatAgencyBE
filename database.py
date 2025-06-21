from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import models



DATABASE_URL = "sqlite:///./cats.db"  # or your DB connection string

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


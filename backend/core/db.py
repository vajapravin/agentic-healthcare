from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from env import DATABASE_URL

# Create the SQLAlchemy engine
# This manages the connection pool to your PostgreSQL container
engine = create_engine(DATABASE_URL, echo=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for your SQL models
Base = declarative_base()

def get_db():
    """
    Dependency to generate a database session per request.
    This ensures connections are cleanly opened and closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
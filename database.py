from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# Inisialisasi engine dan session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Dependency untuk mendapatkan session database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fungsi inisialisasi DB
def init_db():
    from models.models import Base  # Import di dalam untuk menghindari circular import
    Base.metadata.create_all(bind=engine)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Inisialisasi DB (pastikan hanya dipanggil sekali saat startup, atau dari script setup)
def init_db():
    Base.metadata.create_all(bind=engine)

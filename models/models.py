from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Poin(Base):
    __tablename__ = "poin"
    user_id = Column(String, primary_key=True)
    total = Column(Integer, default=0)
    last_telega = Column(DateTime)
    telega_start = Column(DateTime)

class Riwayat(Base):
    __tablename__ = "riwayat"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    type = Column(String)
    amount = Column(Integer)
    time = Column(DateTime)

class Verifikasi(Base):
    __tablename__ = "verifikasi"
    user_id = Column(String, primary_key=True)
    input = Column(String)
    time = Column(DateTime)

class Referral(Base):
    __tablename__ = "referral"
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer = Column(String)
    referred = Column(String)

class Penarikan(Base):
    __tablename__ = "penarikan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    amount = Column(Integer)
    metode = Column(String)
    nomor = Column(String)
    time = Column(DateTime)
    status = Column(String, default="pending")

class CaptchaSession(Base):
    __tablename__ = "captcha_session"
    user_id = Column(String, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

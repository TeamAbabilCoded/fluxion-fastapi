from datetime import datetime
from fastapi import APIRouter
from sqlalchemy.orm import Session
from schemas.schemas import StartSessionRequest
from models.models import User, Poin, Riwayat, Referral, Penarikan, Verifikasi
from database import SessionLocal

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "user route aktif"}

@router.post("/user")
async def create_user(data: StartSessionRequest):
    uid = data.user_id
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=uid).first()
        if user:
            return {"status": "ok", "message": "User sudah ada"}
        
        new_user = User(user_id=uid, created_at=datetime.utcnow())
        db.add(new_user)
        db.commit()
        return {"status": "ok", "message": "User berhasil ditambahkan"}
    finally:
        db.close()
    
@router.get("/saldo/{uid}")
def get_saldo(uid: str):
    db: Session = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    return {"saldo": poin.total if poin else 0}

@router.get("/riwayat/{uid}")
def get_riwayat(uid: str):
    db: Session = SessionLocal()
    hasil = db.query(Riwayat).filter_by(user_id=uid).all()
    return {
        "riwayat": [
            {
                "type": x.type,
                "amount": x.amount,
                "time": x.time.isoformat()
            }
            for x in hasil
        ]
    }

@router.get("/referral/{uid}")
def get_ref(uid: str):
    db: Session = SessionLocal()
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

@router.get("/statistik")
def statistik():
    db: Session = SessionLocal()

    total_user = db.query(User).count()
    total_poin = db.query(Poin).with_entities(Poin.total).all()
    total_tarik = db.query(Penarikan).count()
    total_verifikasi = db.query(Verifikasi).count()

    return {
        "total_user": total_user,
        "total_poin": sum(p[0] for p in total_poin),
        "total_tarik": total_tarik,
        "total_verifikasi": total_verifikasi
    }

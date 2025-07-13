from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.schemas import StartSessionRequest
from models.models import User, Poin, Riwayat, Referral, Penarikan, Verifikasi
from database import get_db  # Ganti SessionLocal manual dengan Depends

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "✅ User route aktif"}

@router.post("/")
async def create_user(data: StartSessionRequest, db: Session = Depends(get_db)):
    uid = data.user_id
    user = db.query(User).filter_by(user_id=uid).first()
    if user:
        return {"status": "ok", "message": "User sudah ada"}
    
    db.add(User(user_id=uid, created_at=datetime.utcnow()))
    db.commit()
    return {"status": "ok", "message": "User berhasil ditambahkan"}

@router.get("/saldo/{uid}")
def get_saldo(uid: str, db: Session = Depends(get_db)):
    poin = db.query(Poin).filter_by(user_id=uid).first()
    return {"saldo": poin.total if poin else 0}

@router.get("/riwayat/{uid}")
def get_riwayat(uid: str, db: Session = Depends(get_db)):
    hasil = db.query(Riwayat).filter_by(user_id=uid).all()
    return {
        "riwayat": [
            {
                "type": x.type,
                "amount": x.amount,
                "time": x.time.isoformat()
            } for x in hasil
        ]
    }

@router.get("/referral/{uid}")
def get_ref(uid: str, db: Session = Depends(get_db)):
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

@router.get("/statistik")
def statistik(db: Session = Depends(get_db)):
    total_user = db.query(User).count()
    total_poin = sum([p.total for p in db.query(Poin).all()])
    total_tarik = db.query(Penarikan).count()
    total_verifikasi = db.query(Verifikasi).count()

    return {
        "total_user": total_user,
        "total_poin": total_poin,
        "total_tarik": total_tarik,
        "total_verifikasi": total_verifikasi
    }

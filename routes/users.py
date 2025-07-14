from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from database import get_db
from models.models import User, Poin, Riwayat, Referral, Penarikan, Verifikasi
from schemas.schemas import StartSessionRequest, ReferralRequest

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
    
    new_user = User(user_id=uid, created_at=datetime.utcnow())
    db.add(new_user)
    db.commit()
    return {"status": "ok", "message": "User berhasil ditambahkan"}

@router.get("/statistik")
def statistik(db: Session = Depends(get_db)):
    total_user = db.query(User).count()
    total_poin = db.query(func.sum(Poin.total)).scalar() or 0  # Lebih aman
    total_tarik = db.query(Penarikan).count()
    pending_tarik = db.query(Penarikan).filter_by(status="pending").count()
    total_verifikasi = db.query(Verifikasi).count()

    return {
        "total_user": total_user,
        "total_poin": total_poin,
        "total_tarik": total_tarik,
        "pending_tarik": pending_tarik,
        "total_verifikasi": total_verifikasi
    }

@router.get("/{uid}")
def get_user(uid: int):
    db = SessionLocal()
    user = db.query(Poin).filter_by(user_id=uid).first()
    
    if not user:
        user = Poin(user_id=uid, total=0)
        db.add(user)
        db.commit()
    
    return {"user_id": uid, "total": user.total}
    
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

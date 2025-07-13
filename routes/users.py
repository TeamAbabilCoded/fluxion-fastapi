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
    
    new_user = User(user_id=uid, created_at=datetime.utcnow())
    db.add(new_user)
    db.commit()
    return {"status": "ok", "message": "User berhasil ditambahkan"}

@router.post("/referral")
async def create_referral(data: ReferralRequest, db: Session = Depends(get_db)):
    # Cek apakah user referral sudah ada
    referrer_exists = db.query(User).filter_by(user_id=data.ref_id).first()
    if not referrer_exists:
        raise HTTPException(status_code=404, detail="Referrer tidak ditemukan")

    # Cegah user referral ke diri sendiri
    if data.user_id == data.ref_id:
        raise HTTPException(status_code=400, detail="Tidak boleh refer ke diri sendiri")

    # Cek apakah sudah pernah direferensikan sebelumnya
    existing = db.query(Referral).filter_by(referred=data.user_id).first()
    if existing:
        return {"status": "ok", "message": "Sudah direferensikan sebelumnya"}

    referral = Referral(referrer=data.ref_id, referred=data.user_id)
    db.add(referral)
    db.commit()
    return {"status": "ok", "message": "Referral dicatat"}

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

from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal
from models.models import Riwayat, Verifikasi, Referral, Poin, User

router = APIRouter()

# 🔄 Riwayat Transaksi
@router.get("/riwayat/{uid}")
def get_riwayat(uid: str):
    db: Session = SessionLocal()
    hasil = db.query(Riwayat).filter_by(user_id=uid).all()
    return {
        "riwayat": [{
            "type": r.type,
            "amount": r.amount,
            "time": r.time.isoformat()
        } for r in hasil]
    }

# ✅ Simpan / Update Verifikasi
@router.post("/verifikasi")
async def simpan_verifikasi(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    inputan = data.get("input")

    db: Session = SessionLocal()
    existing = db.query(Verifikasi).filter_by(user_id=uid).first()
    if not existing:
        verif = Verifikasi(user_id=uid, input=inputan, time=datetime.utcnow())
        db.add(verif)
    else:
        existing.input = inputan
        existing.time = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Verifikasi disimpan"}

# 👥 Jumlah Referral
@router.get("/referral/{uid}")
def get_ref(uid: str):
    db: Session = SessionLocal()
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

# 📊 Statistik Pengguna
@router.get("/statistik")
def statistik():
    db: Session = SessionLocal()
    return {
        "total_user": db.query(User).count(),
        "total_poin": sum([p.total for p in db.query(Poin).all()]),
        "total_tarik": db.query(Riwayat).filter_by(type="penarikan").count(),
        "total_verifikasi": db.query(Verifikasi).count()
    }

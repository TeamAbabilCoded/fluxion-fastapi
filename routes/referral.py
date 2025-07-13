from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.schemas import ReferralRequest
from models.models import Referral, User

router = APIRouter()

@router.post("/referral")
async def create_referral(data: ReferralRequest, db: Session = Depends(get_db)):
    # Pastikan referrer ada
    referrer = db.query(User).filter_by(user_id=data.ref_id).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer tidak ditemukan")

    # Cegah refer ke diri sendiri
    if data.user_id == data.ref_id:
        raise HTTPException(status_code=400, detail="Tidak boleh refer ke diri sendiri")

    # Cek apakah user sudah pernah direferensikan
    existing = db.query(Referral).filter_by(referred=data.user_id).first()
    if existing:
        return {"status": "ok", "message": "Sudah direferensikan sebelumnya"}

    referral = Referral(referrer=data.ref_id, referred=data.user_id)
    db.add(referral)
    db.commit()
    return {"status": "ok", "message": "Referral dicatat"}

@router.get("/referral/{uid}")
def get_ref(uid: str, db: Session = Depends(get_db)):
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

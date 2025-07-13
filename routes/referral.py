from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.schemas import ReferralRequest
from models.models import Referral, User, Poin
from config import BOT_TOKEN
import httpx

router = APIRouter()

@router.post("")
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

    # Catat referral
    referral = Referral(referrer=data.ref_id, referred=data.user_id)
    db.add(referral)

    # Tambahkan poin ke referrer
    poin_referrer = db.query(Poin).filter_by(user_id=data.ref_id).first()
    if not poin_referrer:
        # Jika belum ada data poin, buat baru
        poin_referrer = Poin(user_id=data.ref_id, total=1000)
        db.add(poin_referrer)
    else:
        poin_referrer.total += 1000

    db.commit()
    
    bot_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = "🎉 Kamu mendapatkan Rp 1000 poin karena berhasil mereferensikan user baru!"

    async with httpx.AsyncClient() as client:
        try:
            await client.post(bot_api_url, data={
                "chat_id": data.ref_id,
                "text": message
            })
        except Exception as e:
            print(f"Gagal mengirim notifikasi ke user {data.ref_id}: {e}")

    return {"status": "ok", "message": "Referral dicatat dan poin telah ditambahkan"}

@router.get("/{uid}")
def get_ref(uid: str, db: Session = Depends(get_db)):
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

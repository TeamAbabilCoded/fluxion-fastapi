from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Penarikan, Poin
from schemas.schemas import AjukanTarikRequest, KonfirmasiTarikRequest
from datetime import datetime
import asyncio, httpx
from config import BOT_TOKEN

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@router.post("/ajukan_tarik")
async def ajukan_tarik(data: AjukanTarikRequest):
    uid = data.user_id
    amount = data.amount
    metode = data.metode
    nomor = data.nomor

    db: Session = SessionLocal()
    try:
        poin = db.query(Poin).filter_by(user_id=uid).first()

        if not poin or poin.total < amount:
            raise HTTPException(status_code=400, detail="Saldo tidak cukup")

        poin.total -= amount
        db.add(poin)  # pastikan perubahan poin tersimpan

        tarik = Penarikan(
            user_id=uid,
            amount=amount,
            metode=metode,
            nomor=nomor,
            time=datetime.utcnow(),
            status="pending"
        )
        db.add(tarik)
        db.commit()

        # Notifikasi ke user (opsional tapi disarankan)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": uid,
                    "text": f"✅ Penarikan sebesar Rp{amount:,} via {metode} telah diajukan dan sedang diproses."
                }
            )

        return {"status": "ok", "message": "Penarikan diajukan"}
    finally:
        db.close()
    
@router.post("/konfirmasi_tarik")
async def konfirmasi_tarik(data: KonfirmasiTarikRequest):
    user_id = data.user_id
    jumlah = data.jumlah
    status = data.status

    db = SessionLocal()
    penarikan = db.query(Penarikan).filter_by(
        user_id=user_id, amount=jumlah, status="pending"
    ).first()

    if not penarikan:
        raise HTTPException(status_code=404, detail="Penarikan tidak ditemukan")

    penarikan.status = status

    if status == "ditolak":
        poin = db.query(Poin).filter_by(user_id=user_id).first()
        if poin:
            poin.total += jumlah

    db.commit()

    pesan = "✅ Penarikan diterima" if status == "diterima" else "❌ Penarikan ditolak"
    asyncio.create_task(kirim_notif(user_id, pesan))

    return {"status": "ok", "message": f"Penarikan {status}"}

async def kirim_notif(user_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(BOT_API, data={
            "chat_id": user_id,
            "text": pesan,
            "parse_mode": "Markdown"
        })

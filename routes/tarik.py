from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal
from models.models import Penarikan, Poin
import httpx
import asyncio
from config import BOT_TOKEN

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# 🧾 Ajukan Penarikan oleh user
@router.post("/ajukan_tarik")
async def ajukan_tarik(req: Request):
    data = await req.json()
    uid = int(data.get("user_id"))
    amount = int(data.get("amount"))
    metode = data.get("metode")
    nomor = data.get("nomor")

    if amount < 100_000:
        return {"status": "error", "message": "Minimal penarikan adalah 100.000 poin"}

    db: Session = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()

    if not poin or poin.total < amount:
        return {"status": "error", "message": "Saldo tidak cukup"}

    poin.total -= amount
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
    return {"status": "ok", "message": "Penarikan diajukan"}

# ✅ Admin konfirmasi penarikan
@router.post("/konfirmasi_tarik")
async def konfirmasi_tarik(req: Request):
    try:
        data = await req.json()
        user_id = int(data.get("user_id"))
        jumlah = int(data.get("jumlah"))
        status = data.get("status")

        if not user_id or jumlah <= 0 or status not in ["diterima", "ditolak"]:
            raise HTTPException(status_code=400, detail="Data tidak valid")

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

        # Notifikasi ke user
        pesan = "✅ Penarikan diterima" if status == "diterima" else "❌ Penarikan ditolak"
        asyncio.create_task(kirim_notif(user_id, pesan))

        return {"status": "ok", "message": f"Penarikan {status}"}

    except Exception as e:
        print("❌ INTERNAL ERROR:", e)
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal")

# 🔔 Fungsi notifikasi ke user
async def kirim_notif(user_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(BOT_API, data={
            "chat_id": user_id,
            "text": pesan,
            "parse_mode": "Markdown"
        })

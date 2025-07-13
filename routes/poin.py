from fastapi import APIRouter, Request
from datetime import datetime
from sqlalchemy.orm import Session
from models.models import Poin, Riwayat
from database import SessionLocal
from config import BOT_TOKEN
import httpx

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# 🚀 Start session Mini App
@router.post("/start_session")
async def start_session(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    db = SessionLocal()

    user = db.query(Poin).filter_by(user_id=uid).first()
    if not user:
        user = Poin(user_id=uid, total=0)
        db.add(user)

    user.telega_start = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Session dimulai"}

# 🎁 Tambahkan poin setelah iklan
@router.post("/add_poin")
async def add_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    reward = int(data.get("amount"))
    now = datetime.utcnow()
    db = SessionLocal()

    poin = db.query(Poin).filter_by(user_id=uid).first()
    if not poin or not poin.telega_start:
        return {"status": "error", "message": "Session tidak ditemukan."}

    durasi = (now - poin.telega_start).total_seconds()
    if durasi < 30:
        return {"status": "error", "message": "Stay minimal 30 detik"}
    if durasi > 60:
        return {"status": "error", "message": "Session kedaluwarsa"}

    if poin.last_telega and (now - poin.last_telega).total_seconds() < 10:
        return {"status": "error", "message": "Tunggu 10 detik sebelum klaim lagi"}

    poin.total += reward
    poin.last_telega = now
    db.add(Riwayat(user_id=uid, type="telega_reward", amount=reward, time=now))
    db.commit()

    try:
        await httpx.AsyncClient().post(BOT_API, data={
            "chat_id": uid,
            "text": f"🎉 Kamu mendapatkan Rp {reward} poin dari menonton iklan!",
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print("Gagal kirim notifikasi:", e)

    return {"status": "ok", "message": f"Poin Rp {reward} ditambahkan"}

# 💰 Cek saldo
@router.get("/saldo/{uid}")
def get_saldo(uid: str):
    db = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    return {"saldo": poin.total if poin else 0}

# 🧧 Admin kirim poin
@router.post("/kirim_poin")
async def kirim_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    amount = int(data.get("amount"))
    db = SessionLocal()

    poin = db.query(Poin).filter_by(user_id=uid).first()
    if not poin:
        poin = Poin(user_id=uid, total=0)
        db.add(poin)
    poin.total += amount
    db.commit()
    return {"status": "ok", "message": f"Rp {amount} poin dikirim ke {uid}"}

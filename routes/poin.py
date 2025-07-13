from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Poin, Riwayat, Verifikasi
from schemas.schemas import (
    StartSessionRequest,
    AddPoinRequest,
    KirimPoinRequest,
    VerifikasiRequest,
)
from datetime import datetime
import httpx
from config import BOT_TOKEN

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Start session
@router.post("/start_session")
async def start_session(data: StartSessionRequest):
    uid = data.user_id
    db = SessionLocal()
    user = db.query(Poin).filter_by(user_id=uid).first()
    if not user:
        user = Poin(user_id=uid, total=0)
        db.add(user)
    user.telega_start = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Session dimulai"}

# Tambah poin (klaim reward)
@router.post("/add_poin")
async def add_poin(data: AddPoinRequest):
    uid = data.user_id
    reward = data.amount
    now = datetime.utcnow()
    db = SessionLocal()

    poin = db.query(Poin).filter_by(user_id=uid).first()

    # ✅ Buat otomatis jika user belum ada
    if not poin:
        poin = Poin(user_id=uid, total=0)
        db.add(poin)
        db.commit()
        db.refresh(poin)

    # ✅ Validasi session iklan aktif
    if not poin.telega_start:
        raise HTTPException(status_code=400, detail="Session tidak ditemukan. Silakan mulai ulang.")

    durasi = (now - poin.telega_start).total_seconds()
    if durasi < 30:
        raise HTTPException(status_code=400, detail="Stay minimal 30 detik")
    if durasi > 60:
        raise HTTPException(status_code=400, detail="Session kedaluwarsa")
    if poin.last_telega and (now - poin.last_telega).total_seconds() < 10:
        raise HTTPException(status_code=400, detail="Tunggu 10 detik sebelum klaim lagi")

    poin.total += reward
    poin.last_telega = now
    db.add(Riwayat(user_id=uid, type="telega_reward", amount=reward, time=now))
    db.commit()

    try:
        await send_notif(uid, f"🎉 Kamu mendapatkan Rp {reward} poin dari menonton iklan!")
    except Exception as e:
        print("Gagal kirim notifikasi:", e)

    return {"status": "ok", "message": f"Poin Rp {reward} ditambahkan"}

# Simpan input verifikasi
@router.post("/verifikasi")
async def simpan_verifikasi(data: VerifikasiRequest):
    uid = data.user_id
    inputan = data.input
    db = SessionLocal()
    existing = db.query(Verifikasi).filter_by(user_id=uid).first()
    if not existing:
        db.add(Verifikasi(user_id=uid, input=inputan, time=datetime.utcnow()))
    else:
        existing.input = inputan
        existing.time = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Verifikasi disimpan"}

# Kirim poin ke user (oleh admin)
@router.post("/kirim_poin")
async def kirim_poin(data: KirimPoinRequest):
    uid = data.user_id
    amount = data.amount
    db = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    if not poin:
        poin = Poin(user_id=uid, total=0)
        db.add(poin)
    poin.total += amount
    db.commit()
    return {"status": "ok", "message": f"Rp {amount} poin dikirim ke {uid}"}

# Notifikasi
async def send_notif(user_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(BOT_API, data={
            "chat_id": user_id,
            "text": pesan,
            "parse_mode": "Markdown"
        })

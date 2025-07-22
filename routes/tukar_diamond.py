from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Poin, VoucherGame
from schemas.schemas import TukarDiamondRequest, KonfirmasiVoucherRequest
from datetime import datetime
import httpx
from config import BOT_TOKEN

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ========== TUKAR VOUCHER ==========
@router.post("/tukar_diamond")
async def tukar_diamond(data: TukarDiamondRequest):
    user_id = data.user_id
    game = data.game.upper()
    id_game = data.id_game
    diamond = data.diamond
    total_poin = diamond * 100

    db: Session = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=user_id).first()

    if not poin or poin.total < total_poin:
        raise HTTPException(status_code=400, detail="Saldo poin tidak cukup")

    # Kurangi poin dan simpan
    poin.total -= total_poin
    db.add(poin)

    voucher = VoucherGame(
        user_id=user_id,
        game=game,
        id_game=id_game,
        diamond=diamond,
        time=datetime.utcnow(),
        status="pending"
    )
    db.add(voucher)
    db.commit()

    await kirim_notif(user_id, f"✅ Penukaran {diamond} diamond {game} sedang diproses.")
    return {"status": "ok", "message": "Penukaran berhasil diajukan"}


# ========== KONFIRMASI MANUAL OLEH ADMIN ==========
@router.post("/konfirmasi_voucher")
async def konfirmasi_voucher(data: KonfirmasiVoucherRequest):
    user_id = data.user_id
    jumlah = data.diamond
    status = data.status

    db = SessionLocal()
    voucher = db.query(VoucherGame).filter_by(
        user_id=user_id, diamond=jumlah, status="pending"
    ).first()

    if not voucher:
        raise HTTPException(status_code=404, detail="Penukaran voucher tidak ditemukan")

    voucher.status = status

    if status == "gagal":
        poin = db.query(Poin).filter_by(user_id=user_id).first()
        if poin:
            poin.total += jumlah * 100
            db.add(poin)

    db.commit()

    pesan = (
        f"✅ Penukaran {jumlah} diamond *{voucher.game}* telah dikonfirmasi dan akan segera diproses."
        if status == "sukses"
        else f"❌ Penukaran {jumlah} diamond *{voucher.game}* ditolak. Poin kamu telah dikembalikan."
    )
    await kirim_notif(user_id, pesan)

    return {"status": "ok", "message": f"Penukaran {status}"}


# ========== APPROVE VOUCHER VIA LINK ==========
@router.get("/approve_voucher/{user_id}/{jumlah}")
async def approve_voucher(user_id: str, jumlah: int):
    db = SessionLocal()
    voucher = db.query(VoucherGame).filter_by(
        user_id=user_id, diamond=jumlah, status="pending"
    ).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Permintaan voucher tidak ditemukan")

    voucher.status = "sukses"
    db.commit()

    await kirim_notif(user_id, f"✅ Penukaran {jumlah} diamond {voucher.game} kamu telah disetujui.")
    return {"status": "ok", "message": "Voucher disetujui"}


# ========== REJECT VOUCHER VIA LINK ==========
@router.get("/reject_voucher/{user_id}/{jumlah}")
async def reject_voucher(user_id: str, jumlah: int):
    db = SessionLocal()
    voucher = db.query(VoucherGame).filter_by(
        user_id=user_id, diamond=jumlah, status="pending"
    ).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Permintaan voucher tidak ditemukan")

    voucher.status = "gagal"

    poin = db.query(Poin).filter_by(user_id=user_id).first()
    if poin:
        poin.total += jumlah * 100
        db.add(poin)

    db.commit()

    await kirim_notif(user_id, f"❌ Penukaran {jumlah} diamond {voucher.game} kamu ditolak. Poin telah dikembalikan.")
    return {"status": "ok", "message": "Voucher ditolak"}


# ========== FUNGSI NOTIFIKASI ==========
async def kirim_notif(chat_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(
            BOT_API,
            data={
                "chat_id": chat_id,
                "text": pesan,
                "parse_mode": "Markdown"
            }
        )

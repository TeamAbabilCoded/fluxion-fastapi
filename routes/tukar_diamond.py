from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Poin, VoucherGame
from datetime import datetime
import httpx
from config import BOT_TOKEN

router = APIRouter()
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

class TukarDiamondRequest(BaseModel):
    user_id: str
    game: str
    id_game: str
    diamond: int

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

    # Kurangi poin
    poin.total -= total_poin
    db.add(poin)

    # Simpan riwayat penukaran
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

    # Kirim notifikasi ke user
    await kirim_notif(user_id, f"✅ Penukaran {diamond} diamond {game} sedang diproses.")

    return {"status": "ok", "message": "Penukaran berhasil diajukan"}

async def kirim_notif(chat_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(BOT_API, data={"chat_id": chat_id, "text": pesan})

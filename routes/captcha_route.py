from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.models import CaptchaSession
from datetime import datetime
import uuid

from schemas.captcha_schema import UserIdPayload, CaptchaPayload
from captcha.verify_captcha import verify_hcaptcha_token
router = APIRouter()

@router.post("/start_session")
def start_captcha_session(payload: UserIdPayload, db: Session = Depends(get_db)):
    user_id = payload.user_id
    token = str(uuid.uuid4())
    new_session = CaptchaSession(
        user_id=user_id,
        token=token,
        is_used=False,
        created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    return {"status": "success", "token": token}

@router.post("/verify_captcha")
async def verify_captcha(payload: CaptchaPayload, db: Session = Depends(get_db)):
    # 1. Verifikasi ke hCaptcha
    is_valid = await verify_hcaptcha_token(payload.token)
    if not is_valid:
        return {"status": "error", "message": "Captcha tidak valid"}

    # 2. Verifikasi session token
    session = db.query(CaptchaSession).filter_by(
        user_id=payload.user_id,
        token=payload.session_token,
        is_used=False
    ).first()

    if not session:
        return {"status": "error", "message": "Sesi captcha tidak ditemukan atau sudah digunakan"}

    # 3. Tandai sebagai sudah digunakan
    session.is_used = True
    db.commit()

    return {"status": "success", "message": "Captcha berhasil diverifikasi"}


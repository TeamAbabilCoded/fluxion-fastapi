from fastapi import APIRouter
from schemas.captcha_schema import CaptchaPayload
from captcha.verify_captcha import verify_hcaptcha_token

router = APIRouter()

@router.post("/verify_captcha")
async def verify_captcha(payload: CaptchaPayload):
    is_valid = await verify_hcaptcha_token(payload.token)
    if is_valid:
        # Di sini kamu bisa tandai user sudah lolos captcha
        return {"status": "ok", "message": "Captcha valid"}
    return {"status": "error", "message": "Captcha tidak valid"}

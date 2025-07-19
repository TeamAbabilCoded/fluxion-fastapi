import httpx
import os

HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET", "ES_216ccc62ace34159b5e06d521a833cfd")  # Ganti dengan yang asli

async def verify_hcaptcha_token(token: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post("https://hcaptcha.com/siteverify", data={
            'response': token,
            'secret': HCAPTCHA_SECRET
        })
        result = response.json()
        return result.get("success", False)

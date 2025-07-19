from pydantic import BaseModel

class CaptchaPayload(BaseModel):
    token: str
    user_id: str
    session_token: str 

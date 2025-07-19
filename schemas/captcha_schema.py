from pydantic import BaseModel

class UserIdPayload(BaseModel):
    user_id: str

class CaptchaPayload(BaseModel):
    token: str
    user_id: str
    session_token: str 

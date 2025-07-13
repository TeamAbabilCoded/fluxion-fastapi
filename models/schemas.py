from pydantic import BaseModel

class StartSessionRequest(BaseModel):
    user_id: str
    username: str = "

class ReferralRequest(BaseModel):
    user_id: str
    ref_id: str

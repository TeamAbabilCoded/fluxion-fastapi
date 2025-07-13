from pydantic import BaseModel

class StartSessionRequest(BaseModel):
    user_id: str
    username: str = "

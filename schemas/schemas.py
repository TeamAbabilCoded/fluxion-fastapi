from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime

# Validasi numeric
UserIDStr = Annotated[str, Field(description="ID user, bebas string")]
UserIDInt = Annotated[int, Field(ge=1, description="ID user sebagai integer")]
PositiveInt = Annotated[int, Field(gt=0)]
MinimalTarik = Annotated[int, Field(ge=100_000)]
NonEmptyStr = Annotated[str, Field(min_length=1)]
NomorStr = Annotated[str, Field(min_length=5)]
StatusTarik = Annotated[str, Field(pattern="^(diterima|ditolak)$")]


class StartSessionRequest(BaseModel):
    user_id: str
    username: str = "

class ReferralRequest(BaseModel):
    user_id: str
    ref_id: str
    
class StartSessionRequest(BaseModel):
    user_id: UserIDStr


class AddPoinRequest(BaseModel):
    user_id: UserIDStr
    amount: PositiveInt


class KirimPoinRequest(BaseModel):
    user_id: UserIDStr
    amount: PositiveInt


class AjukanTarikRequest(BaseModel):
    user_id: UserIDInt
    amount: MinimalTarik
    metode: NonEmptyStr
    nomor: NomorStr


class KonfirmasiTarikRequest(BaseModel):
    user_id: UserIDInt
    jumlah: PositiveInt
    status: StatusTarik


class VerifikasiRequest(BaseModel):
    user_id: UserIDStr
    input: NonEmptyStr

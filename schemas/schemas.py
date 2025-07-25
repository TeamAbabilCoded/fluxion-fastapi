from pydantic import BaseModel, Field, PositiveInt
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
StatusVoucher = Annotated[str, Field(pattern="^(sukses|gagal)$")] 

class StartSessionRequest(BaseModel):
    user_id: str
    username: str = ""

class StartSessionRequest(BaseModel):
    user_id: str

class ReferralRequest(BaseModel):
    user_id: str
    ref_id: str

class AddPoinRequest(BaseModel):
    user_id: UserIDStr
    amount: PositiveInt


class KirimPoinRequest(BaseModel):
    user_id: int
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


class TukarDiamondRequest(BaseModel):
    user_id: str
    game: str
    id_game: str
    diamond: int

class KonfirmasiVoucherRequest(BaseModel):  # ← Tambahkan ini
    user_id: str
    diamond: int
    status: StatusVoucher

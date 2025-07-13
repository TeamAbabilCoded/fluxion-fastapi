from pydantic import BaseModel, Field, conint, constr

class StartSessionRequest(BaseModel):
    user_id: str = Field(..., description="ID user, bebas string apa saja")

class AddPoinRequest(BaseModel):
    user_id: str = Field(..., description="ID user, bebas string")
    amount: conint(gt=0) = Field(..., description="Jumlah poin, harus lebih dari 0")

class KirimPoinRequest(BaseModel):
    user_id: str = Field(..., description="ID user, bebas string")
    amount: conint(gt=0) = Field(..., description="Jumlah poin yang dikirim, harus > 0")

class AjukanTarikRequest(BaseModel):
    user_id: int = Field(..., description="ID user sebagai integer")
    amount: conint(ge=100000) = Field(..., description="Minimal penarikan 100.000")
    metode: constr(min_length=1) = Field(..., description="Metode penarikan, contoh: Dana, OVO")
    nomor: constr(min_length=5) = Field(..., description="Nomor tujuan penarikan")

class KonfirmasiTarikRequest(BaseModel):
    user_id: int = Field(..., description="ID user sebagai integer")
    jumlah: conint(gt=0) = Field(..., description="Jumlah penarikan")
    status: constr(regex="^(diterima|ditolak)$") = Field(..., description="Status penarikan, diterima atau ditolak")

class VerifikasiRequest(BaseModel):
    user_id: str = Field(..., description="ID user, bebas string")
    input: str = Field(..., description="Input verifikasi dari user")

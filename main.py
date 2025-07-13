from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Router modular
from schemas.schemas import ReferralRequest
from routes.auth import router as auth_router
from routes.tarik import router as tarik_router
from routes.poin import router as poin_router
from routes.users import router as user_router
from routes.auth import router as auth_router
from models.models import Referral, User
from routes.referral import router as referral_router

# Inisialisasi DB
from database import init_db

app = FastAPI(title="Fluxion Faucet API")

# Inisialisasi database
init_db()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Static files dan templates (jika ada frontend/template)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include semua router dengan prefix
app.include_router(auth_router, prefix="/auth")
app.include_router(tarik_router, prefix="/tarik")
app.include_router(poin_router, prefix="/poin")
app.include_router(user_router, prefix="/user")
app.include_router(referral_router, prefix="")
app.include_router(auth_router)

# Root endpoint
@app.get("/")
def root():
    return {"status": "ok", "message": "Fluxion Faucet API aktif"}

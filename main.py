from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Router modular
from routes.auth import router as auth_router
from routes.tarik import router as tarik_router
from routes.poin import router as poin_router
from routes.users import router as user_router
from routes.referral import router as referral_router
from routes import tukar_diamond
from routes import approve_user

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

# Include route admin panel
app.include_router(auth_router)
app.include_router(approve_user.router)
app.include_router(tukar_diamond.router)

# Include semua router dengan prefix
app.include_router(tarik_router, prefix="/tarik")
app.include_router(poin_router, prefix="/poin")
app.include_router(user_router, prefix="/user")
app.include_router(referral_router, prefix="/referral")

# Root endpoint
@app.get("/")
def root():
    return {"status": "ok", "message": "Fluxion Faucet API aktif"}

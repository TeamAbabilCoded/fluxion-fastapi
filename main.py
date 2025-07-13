from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Router modular
from routes.auth import router as auth_router
from routes.tarik import router as tarik_router
from routes.poin import router as poin_router
from routes.users import router as user_router

# Inisialisasi DB (membuat tabel jika belum ada)
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

# Static files dan templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include semua router
app.include_router(auth_router)
app.include_router(tarik_router)
app.include_router(poin_router)
app.include_router(user_router)

# Root endpoint
@app.get("/")
def root():
    return {"status": "ok", "message": "Fluxion Faucet API aktif"}

import os
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import BOT_TOKEN, ADMIN_PASSWORD, DATABASE_URL
import httpx
from aiogram import Bot

BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

router = APIRouter()
app = FastAPI()
app.include_router(router)
bot = Bot(token=BOT_TOKEN)

# CORS & Static
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# DB Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ========================== MODELS ==========================
class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Poin(Base):
    __tablename__ = "poin"
    user_id = Column(String, primary_key=True)
    total = Column(Integer, default=0)
    last_telega = Column(DateTime)
    telega_start = Column(DateTime)

class Riwayat(Base):
    __tablename__ = "riwayat"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    type = Column(String)
    amount = Column(Integer)
    time = Column(DateTime)

class Verifikasi(Base):
    __tablename__ = "verifikasi"
    user_id = Column(String, primary_key=True)
    input = Column(String)
    time = Column(DateTime)

class Referral(Base):
    __tablename__ = "referral"
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer = Column(String)
    referred = Column(String)

class Penarikan(Base):
    __tablename__ = "penarikan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    amount = Column(Integer)
    metode = Column(String)
    nomor = Column(String)
    time = Column(DateTime)
    status = Column(String, default="pending")  # Tambahkan ini

Base.metadata.create_all(bind=engine)

# ========================== ROUTES ==========================
@app.get("/")
def root():
    return {"status": "ok", "message": "Fluxion API aktif"}

@app.get("/dashboard-admin", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/dashboard-admin", response_class=HTMLResponse)
def dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Password salah. Silakan coba lagi.",
            "success": False
        })
    db = SessionLocal()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "success": True,
        "data": db.query(Poin).all(),
        "penarikan": db.query(Penarikan).all(),
        "verifikasi": db.query(Verifikasi).all(),
        "riwayat": db.query(Riwayat).all(),
        "user": db.query(User).all(),
        "ref": db.query(Referral).all()
    })

@app.post("/start_session")
async def start_session(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    db = SessionLocal()
    user = db.query(Poin).filter_by(user_id=uid).first()
    if not user:
        user = Poin(user_id=uid, total=0)
        db.add(user)
    user.telega_start = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Session dimulai"}

@app.post("/add_poin")
async def add_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    reward = int(data.get("amount"))
    now = datetime.utcnow()
    db = SessionLocal()

    poin = db.query(Poin).filter_by(user_id=uid).first()
    if not poin or not poin.telega_start:
        return {"status": "error", "message": "Session tidak ditemukan."}

    durasi = (now - poin.telega_start).total_seconds()
    if durasi < 30:
        return {"status": "error", "message": "Stay minimal 30 detik"}
    if durasi > 60:
        return {"status": "error", "message": "Session kedaluwarsa"}

    if poin.last_telega and (now - poin.last_telega).total_seconds() < 10:
        return {"status": "error", "message": "Tunggu 10 detik sebelum klaim lagi"}

    poin.total += reward
    poin.last_telega = now
    db.add(Riwayat(user_id=uid, type="telega_reward", amount=reward, time=now))
    db.commit()

    try:
        await bot.send_message(int(uid), f"🎉 Kamu mendapatkan Rp {reward} poin dari menonton iklan!")
    except Exception as e:
        print("Gagal kirim notifikasi:", e)

    return {"status": "ok", "message": f"Poin Rp {reward} ditambahkan"}

@app.get("/saldo/{uid}")
def get_saldo(uid: str):
    db = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    return {"saldo": poin.total if poin else 0}

@app.get("/riwayat/{uid}")
def get_riwayat(uid: str):
    db = SessionLocal()
    hasil = db.query(Riwayat).filter_by(user_id=uid).all()
    return {"riwayat": [{
        "type": x.type,
        "amount": x.amount,
        "time": x.time.isoformat()
    } for x in hasil]}

@app.post("/verifikasi")
async def simpan_verifikasi(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    inputan = data.get("input")
    db = SessionLocal()
    existing = db.query(Verifikasi).filter_by(user_id=uid).first()
    if not existing:
        verif = Verifikasi(user_id=uid, input=inputan, time=datetime.utcnow())
        db.add(verif)
    else:
        existing.input = inputan
        existing.time = datetime.utcnow()
    db.commit()
    return {"status": "ok", "message": "Verifikasi disimpan"}

@app.post("/kirim_poin")
async def kirim_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    amount = int(data.get("amount"))
    db = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    if not poin:
        poin = Poin(user_id=uid, total=0)
        db.add(poin)
    poin.total += amount
    db.commit()
    return {"status": "ok", "message": f"Rp {amount} poin dikirim ke {uid}"}

@app.get("/referral/{uid}")
def get_ref(uid: str):
    db = SessionLocal()
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

@app.post("/ajukan_tarik")
async def ajukan_tarik(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    amount = int(data.get("amount"))
    metode = data.get("metode")
    nomor = data.get("nomor")

    if amount < 100_000:
        return {"status": "error", "message": "Minimal penarikan adalah 100.000 poin"}

    db = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()

    if not poin or poin.total < amount:
        return {"status": "error", "message": "Saldo tidak cukup"}

    poin.total -= amount
    tarik = Penarikan(
        user_id=uid,
        amount=amount,
        metode=metode,
        nomor=nomor,
        time=datetime.utcnow(),
        status="pending"  # Harus pending dulu
    )
    db.add(tarik)
    db.commit()

    return {"status": "ok", "message": "Penarikan diajukan"}

@router.post("/konfirmasi_tarik")
async def konfirmasi_tarik(req: Request):
    data = await req.json()
    try:
        user_id = int(data.get("user_id"))
        jumlah = int(data.get("jumlah", 0))
        status = data.get("status")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Data tidak valid")

    if jumlah <= 0 or status not in ["diterima", "ditolak"]:
        raise HTTPException(status_code=400, detail="Data tidak valid")

    db = SessionLocal()
    try:
        penarikan = db.query(Penarikan).filter_by(
            user_id=user_id, amount=jumlah, status="pending"
        ).first()
        if not penarikan:
            raise HTTPException(status_code=404, detail="Penarikan tidak ditemukan")

        penarikan.status = status
        if status == "ditolak":
            poin = db.query(Poin).filter_by(user_id=user_id).first()
            if poin:
                poin.total += jumlah

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    finally:
        db.close()

    asyncio.create_task(kirim_notif(user_id, f"✅ Penarikan diterima" if status=="diterima" else "❌ Penarikan ditolak"))

    return {"status": "ok", "message": f"Penarikan {status}"}

# Fungsi notifikasi Telegram
async def kirim_notif(user_id, pesan):
    async with httpx.AsyncClient() as client:
        await client.post(BOT_API, data={
            "chat_id": user_id,
            "text": pesan,
            "parse_mode": "Markdown"
        })
    
app.include_router(router)
    
@app.post("/broadcast")
async def broadcast(request: Request):
    form = await request.form()
    pesan = form["pesan"]
    db = SessionLocal()
    semua = db.query(User).all()
    sukses, gagal = 0, 0
    async with httpx.AsyncClient() as client:
        for u in semua:
            try:
                await client.post("http://159.89.195.47:8000/notif", json={
                    "user_id": u.user_id,
                    "message": f"📢 Pesan dari Admin:\n\n{pesan}"
                })
                sukses += 1
            except:
                gagal += 1
    return HTMLResponse(f"<h3>✅ Broadcast selesai!</h3><p>Sukses: {sukses} | Gagal: {gagal}</p><a href='/dashboard-admin'>🔙 Kembali</a>")

@app.get("/statistik")
def statistik():
    db = SessionLocal()
    return {
        "total_user": db.query(User).count(),
        "total_poin": sum([p.total for p in db.query(Poin).all()]),
        "total_tarik": db.query(Penarikan).count(),
        "total_verifikasi": db.query(Verifikasi).count()
    }

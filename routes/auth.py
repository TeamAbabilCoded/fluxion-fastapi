from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from config import ADMIN_PASSWORD
from models.models import User, Poin, Penarikan, Verifikasi, Riwayat, Referral
import httpx

router = APIRouter()

# Halaman Login Admin
@router.get("/dashboard-admin", response_class=HTMLResponse)
def login(request: Request):
    return request.app.templates.TemplateResponse("login.html", {"request": request})

# Proses Login & Tampilkan Dashboard
@router.post("/dashboard-admin", response_class=HTMLResponse)
def dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return request.app.templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Password salah. Silakan coba lagi.",
            "success": False
        })

    db: Session = SessionLocal()
    return request.app.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "success": True,
        "data": db.query(Poin).all(),
        "penarikan": db.query(Penarikan).all(),
        "verifikasi": db.query(Verifikasi).all(),
        "riwayat": db.query(Riwayat).all(),
        "user": db.query(User).all(),
        "ref": db.query(Referral).all()
    })

# Broadcast Pesan ke Semua User
@router.post("/broadcast", response_class=HTMLResponse)
async def broadcast(request: Request):
    form = await request.form()
    pesan = form["pesan"]
    db = SessionLocal()
    semua = db.query(User).all()
    sukses, gagal = 0, 0
    async with httpx.AsyncClient() as client:
        for u in semua:
            try:
                await client.post("http://localhost:8000/notif", json={
                    "user_id": u.user_id,
                    "message": f"📢 Pesan dari Admin:\n\n{pesan}"
                })
                sukses += 1
            except:
                gagal += 1
    return HTMLResponse(f"<h3>✅ Broadcast selesai!</h3><p>Sukses: {sukses} | Gagal: {gagal}</p><a href='/dashboard-admin'>🔙 Kembali</a>")

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from config import ADMIN_PASSWORD
from models.models import User, Poin, Penarikan, Verifikasi, Riwayat, Referral
from fastapi.templating import Jinja2Templates
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Halaman Login Admin
@router.get("/dashboard-admin", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Proses Login & Tampilkan Dashboard
@router.post("/dashboard-admin", response_class=HTMLResponse)
def dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Password salah. Silakan coba lagi.",
            "success": False
        })

    db: Session = SessionLocal()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "success": True,
        "data": db.query(Poin).all(),
        "penarikan": db.query(Penarikan).filter(Penarikan.status == "pending").all(),
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
                await client.post("http://159.89.195.47:8000/notif", json={
                    "user_id": u.user_id,
                    "message": f"{pesan}"
                })
                sukses += 1
            except:
                gagal += 1
    return HTMLResponse(f"<h3>✅ Broadcast selesai!</h3><p>Sukses: {sukses} | Gagal: {gagal}</p><a href='/dashboard-admin'>🔙 Kembali</a>")

# Tambahan: API Dashboard Admin JSON
@router.get("/admin/dashboard_api")
def admin_dashboard_api(db: Session = Depends(get_db)):
    total_user = db.query(User).count()
    total_poin = db.query(Poin).with_entities(Poin.total).all()
    jumlah_referral = db.query(Referral).count()
    total_penarikan = db.query(Penarikan).count()
    jumlah_diterima = db.query(Penarikan).filter_by(status="diterima").count()
    jumlah_terverifikasi = db.query(Verifikasi).count()

    total_semua_poin = sum(p[0] for p in total_poin) if total_poin else 0

    return {
        "total_user": total_user,
        "total_poin": total_semua_poin,
        "jumlah_referral": jumlah_referral,
        "total_penarikan": total_penarikan,
        "penarikan_diterima": jumlah_diterima,
        "user_terverifikasi": jumlah_terverifikasi
    }

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    db: Session = SessionLocal()
    
    user = db.query(User).all()
    data = db.query(Poin).all()
    penarikan = db.query(Penarikan).filter_by(status="pending").all()
    verifikasi = db.query(Verifikasi).all()
    voucher = db.query(VoucherGame).filter(VoucherGame.status.in_(["pending", "sukses", "gagal"])).all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user,
        "data": data,
        "penarikan": penarikan,
        "verifikasi": verifikasi,
        "voucher": voucher  # ini penting
    })

import os, json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import ADMIN_PASSWORD
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Form

from aiogram import Bot
from config import BOT_TOKEN  # pastikan file config.py tersedia dan di-deploy juga

bot = Bot(token=BOT_TOKEN)

app = FastAPI()

POIN_FILE = "poin.json"
RIWAYAT_FILE = "riwayat.json"
TARIKAN_FILE = "penarikan.json"
VERIFIKASI_FILE = "verifikasi.json"
USER_FILE = "user.json"
REF_FILE = "referral.json"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti ke ["https://miniapp-fluxion-faucet.vercel.app"] jika mau aman
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "success": True,
        "data": load_json(POIN_FILE),
        "penarikan": load_json(TARIKAN_FILE),
        "verifikasi": load_json(VERIFIKASI_FILE),
        "riwayat": load_json(RIWAYAT_FILE),
        "user": load_json(USER_FILE),
        "ref": load_json(REF_FILE)
    })
    
def load_json(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.get("/")
def root():
    return {"status": "ok", "message": "Fluxion API aktif"}

@app.post("/start_session")
async def start_session(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    poin = load_json(POIN_FILE)
    poin[f"{uid}_telega_start"] = datetime.now().isoformat()
    save_json(POIN_FILE, poin)
    return {"status": "ok", "message": "Session dimulai"}

@app.post("/add_poin")
async def add_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    reward = int(data.get("amount"))
    poin = load_json(POIN_FILE)
    riwayat = load_json(RIWAYAT_FILE)
    now = datetime.now()

    start_str = poin.get(f"{uid}_telega_start")
    if not start_str:
        return {"status": "error", "message": "Session tidak ditemukan."}

    start_time = datetime.fromisoformat(start_str)
    durasi = (now - start_time).total_seconds()

    if durasi < 30:
        return {"status": "error", "message": "Stay minimal 30 detik"}
    if durasi > 60:
        return {"status": "error", "message": "Session kedaluwarsa"}

    last_claim_str = poin.get(f"{uid}_last_telega", "1970-01-01T00:00:00")
    last_claim = datetime.fromisoformat(last_claim_str)
    if (now - last_claim).total_seconds() < 10:
        return {"status": "error", "message": "Tunggu 10 detik sebelum klaim lagi"}

    poin[uid] = poin.get(uid, 0) + reward
    poin[f"{uid}_last_telega"] = now.isoformat()
    save_json(POIN_FILE, poin)

    riwayat.setdefault(uid, []).append({
        "type": "telega_reward",
        "amount": reward,
        "time": now.isoformat()
    })
    save_json(RIWAYAT_FILE, riwayat)

    # Kirim notifikasi Telegram
    try:
        await bot.send_message(int(uid), f"🎉 Kamu mendapatkan {reward} poin dari menonton iklan!")
    except Exception as e:
        print("Gagal kirim notifikasi:", e)

    return {"status": "ok", "message": f"Poin {reward} ditambahkan"}

@app.get("/saldo/{uid}")
async def get_saldo(uid: str):
    poin = load_json(POIN_FILE)
    return {"saldo": poin.get(uid, 0)}

@app.get("/riwayat/{uid}")
async def get_riwayat(uid: str):
    riwayat = load_json(RIWAYAT_FILE)
    return {"riwayat": riwayat.get(uid, [])}

@app.post("/verifikasi")
async def simpan_verifikasi(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    inputan = data.get("input")
    verif = load_json(VERIFIKASI_FILE)
    verif[uid] = {
        "input": inputan,
        "time": datetime.now().isoformat()
    }
    save_json(VERIFIKASI_FILE, verif)
    return {"status": "ok", "message": "Verifikasi disimpan"}

@app.post("/kirim_poin")
async def kirim_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    amount = int(data.get("amount"))
    poin = load_json(POIN_FILE)
    poin[uid] = poin.get(uid, 0) + amount
    save_json(POIN_FILE, poin)
    return {"status": "ok", "message": f"{amount} poin dikirim ke {uid}"}

@app.get("/referral/{uid}")
async def get_ref(uid: str):
    ref = load_json(REF_FILE)
    return {"jumlah": len(ref.get(uid, []))}

@app.post("/ajukan_tarik")
async def ajukan_tarik(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    amount = int(data.get("amount"))
    metode = data.get("metode")
    nomor = data.get("nomor")

    poin = load_json(POIN_FILE)
    if poin.get(uid, 0) < amount:
        return {"status": "error", "message": "Saldo tidak cukup"}

    penarikan = load_json(TARIKAN_FILE)
    penarikan.setdefault(uid, []).append({
        "amount": amount,
        "metode": metode,
        "nomor": nomor,
        "time": datetime.now().isoformat()
    })
    save_json(TARIKAN_FILE, penarikan)

    poin[uid] -= amount
    save_json(POIN_FILE, poin)

    return {"status": "ok", "message": "Penarikan diajukan"}

@app.post("/broadcast")
async def broadcast(request: Request):
    form = await request.form()
    pesan = form['pesan']
    user = load_json(USER_FILE)
    for uid in user.keys():
        try:
            await bot.send_message(int(uid), f"📢 Pesan dari Admin:\n\n{pesan}")
        except:
            continue
    return HTMLResponse("<h3>✅ Pesan berhasil dikirim!</h3><a href='/dashboard-admin'>🔙 Kembali</a>")

@app.get("/statistik")
async def statistik():
    user = load_json(USER_FILE)
    poin = load_json(POIN_FILE)
    verif = load_json(VERIFIKASI_FILE)
    tarik = load_json(TARIKAN_FILE)

    return {
        "total_user": len(user),
        "total_poin": sum(v for k, v in poin.items() if not k.endswith("_telega_start") and not k.endswith("_last_telega")),
        "total_tarik": sum(len(x) for x in tarik.values()),
        "total_verifikasi": len(verif)
    }

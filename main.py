import os, json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()

# Lokasi file JSON
POIN_FILE = "poin.json"
RIWAYAT_FILE = "riwayat.json"

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# Aktifkan CORS supaya Mini App bisa akses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # atau ["https://miniapp-fluxion-faucet.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# lalu lanjutkan seperti biasa
@app.get("/")
async def root():
    return {"status": "ok", "message": "Fluxion Faucet API aktif"}

@app.post("/start_session")
async def start_session(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    now = datetime.now().isoformat()

    poin = load_json(POIN_FILE)
    poin[f"{uid}_telega_start"] = now
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
        return {"status": "error", "message": "Minimal stay 30 detik di iklan"}
    if durasi > 60:
        return {"status": "error", "message": "Session kedaluwarsa, silakan mulai ulang"}

    # Cegah spam
    last_claim_str = poin.get(f"{uid}_last_telega", "1970-01-01T00:00:00")
    last_claim = datetime.fromisoformat(last_claim_str)
    if (now - last_claim).total_seconds() < 10:
        return {"status": "error", "message": "Tunggu 10 detik sebelum klaim lagi."}

    # Tambah poin
    poin[uid] = poin.get(uid, 0) + reward
    poin[f"{uid}_last_telega"] = now.isoformat()
    save_json(POIN_FILE, poin)

    # Catat riwayat
    riwayat.setdefault(uid, []).append({
        "type": "telega_reward",
        "amount": reward,
        "time": now.isoformat()
    })
    save_json(RIWAYAT_FILE, riwayat)

    return {"status": "ok", "message": f"Poin {reward} berhasil ditambahkan"}


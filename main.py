import os, json
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

# CORS agar bisa diakses dari Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Bisa diganti domain tertentu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File JSON
POIN_FILE = "poin.json"
RIWAYAT_FILE = "riwayat.json"
VERIFIKASI_FILE = "verifikasi.json"
TARIKAN_FILE = "tarikan.json"

# Utils
def load_json(filename):
    if not os.path.exists(filename): return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Routes
@app.get("/")
async def root():
    return {"status": "ok", "message": "Fluxion Faucet API aktif"}

@app.get("/saldo/{uid}")
async def get_saldo(uid: str):
    poin = load_json(POIN_FILE)
    return {"saldo": poin.get(uid, 0)}

@app.get("/riwayat/{uid}")
async def get_riwayat(uid: str):
    riwayat = load_json(RIWAYAT_FILE).get(uid, [])
    return {"riwayat": riwayat[-5:]}

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

    last_claim_str = poin.get(f"{uid}_last_telega", "1970-01-01T00:00:00")
    last_claim = datetime.fromisoformat(last_claim_str)
    if (now - last_claim).total_seconds() < 10:
        return {"status": "error", "message": "Tunggu 10 detik sebelum klaim lagi."}

    poin[uid] = poin.get(uid, 0) + reward
    poin[f"{uid}_last_telega"] = now.isoformat()
    save_json(POIN_FILE, poin)

    riwayat.setdefault(uid, []).append({
        "type": "telega_reward",
        "amount": reward,
        "time": now.isoformat()
    })
    save_json(RIWAYAT_FILE, riwayat)

    return {"status": "ok", "message": f"Poin {reward} berhasil ditambahkan"}

@app.post("/verifikasi")
async def verifikasi(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    input_data = str(data.get("input"))

    verifikasi = load_json(VERIFIKASI_FILE)
    verifikasi[uid] = {
        "input": input_data,
        "time": datetime.now().isoformat()
    }
    save_json(VERIFIKASI_FILE, verifikasi)

    return {"status": "ok", "message": "Verifikasi berhasil disimpan"}

@app.post("/tarik")
async def tarik(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    jumlah = int(data.get("jumlah"))
    metode = str(data.get("metode"))
    nomor = str(data.get("nomor"))

    poin = load_json(POIN_FILE)
    if poin.get(uid, 0) < jumlah:
        return {"status": "error", "message": "Saldo tidak cukup"}

    penarikan = load_json(TARIKAN_FILE)
    penarikan.setdefault(uid, []).append({
        "amount": jumlah,
        "metode": metode,
        "nomor": nomor,
        "time": datetime.now().isoformat()
    })
    save_json(TARIKAN_FILE, penarikan)

    poin[uid] -= jumlah
    save_json(POIN_FILE, poin)

    return {"status": "ok", "message": "Penarikan diajukan"}

@app.post("/kirim_poin")
async def kirim_poin(req: Request):
    data = await req.json()
    uid = str(data.get("user_id"))
    jumlah = int(data.get("jumlah"))

    poin = load_json(POIN_FILE)
    poin[uid] = poin.get(uid, 0) + jumlah
    save_json(POIN_FILE, poin)

    return {"status": "ok", "message": f"Poin {jumlah} berhasil dikirim ke {uid}"}

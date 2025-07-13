from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Poin, Riwayat, Referral, User, Verifikasi, Penarikan

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "user route aktif"}

@router.post("/user")
async def create_user(data: StartSessionRequest):
    uid = data.user_id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=uid).first()
    if not user:
        user = User(user_id=uid, created_at=datetime.utcnow())
        db.add(user)
        db.commit()
    return {"status": "ok", "message": "User ditambahkan"}
    
@router.get("/saldo/{uid}")
def get_saldo(uid: str):
    db: Session = SessionLocal()
    poin = db.query(Poin).filter_by(user_id=uid).first()
    return {"saldo": poin.total if poin else 0}

@router.get("/riwayat/{uid}")
def get_riwayat(uid: str):
    db: Session = SessionLocal()
    hasil = db.query(Riwayat).filter_by(user_id=uid).all()
    return {
        "riwayat": [
            {
                "type": x.type,
                "amount": x.amount,
                "time": x.time.isoformat()
            }
            for x in hasil
        ]
    }

@router.get("/referral/{uid}")
def get_ref(uid: str):
    db: Session = SessionLocal()
    jumlah = db.query(Referral).filter_by(referrer=uid).count()
    return {"jumlah": jumlah}

@router.get("/statistik")
def statistik():
    db: Session = SessionLocal()

    total_user = db.query(User).count()
    total_poin = db.query(Poin).with_entities(Poin.total).all()
    total_tarik = db.query(Penarikan).count()
    total_verifikasi = db.query(Verifikasi).count()

    return {
        "total_user": total_user,
        "total_poin": sum(p[0] for p in total_poin),
        "total_tarik": total_tarik,
        "total_verifikasi": total_verifikasi
    }

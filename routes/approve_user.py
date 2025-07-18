from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.approved_user import ApprovedUser
from database import get_db

router = APIRouter()

@router.post("/approve_user/{user_id}")
async def approve_user(user_id: int, db: Session = Depends(get_db)):
    existing = db.query(ApprovedUser).filter(ApprovedUser.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User sudah di-approve")

    new_user = ApprovedUser(user_id=user_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": user_id}

@router.get("/approved/{user_id}")
async def check_approved(user_id: int, db: Session = Depends(get_db)):
    user = db.query(ApprovedUser).filter(ApprovedUser.user_id == user_id).first()
    return {"approved": bool(user)}

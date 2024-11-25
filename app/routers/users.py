from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, dependencies

router = APIRouter()

@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    return crud.create_user(db, user)

@router.post("/login/")
def login_user(login: schemas.LoginRequest, db: Session = Depends(dependencies.get_db)):
    user = db.query(User).filter(User.email == login.username).first()
    if user is None or not bcrypt.checkpw(login.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")
    return {"message": "Inicio de sesión exitoso", "name": user.name}

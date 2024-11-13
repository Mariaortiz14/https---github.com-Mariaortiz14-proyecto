from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import re
from pydantic import BaseModel, EmailStr, root_validator
from datetime import datetime
from typing import Optional
import bcrypt


DATABASE_URL = "mysql+pymysql://root:00000@localhost/happenit"
PROFILE_IMAGE_PATH = "static/profile_images"
if not os.path.exists(PROFILE_IMAGE_PATH):
    os.makedirs(PROFILE_IMAGE_PATH)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


Base.metadata.create_all(bind=engine)


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=True)
    phone = Column(String(15), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(DateTime)
    location = Column(String)


class UserCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    phone: str
    email: EmailStr
    password: str
    confirm_password: str  

    @root_validator(pre=True)
    def check_password(cls, values):
        password = values.get('password')
        confirm_password = values.get('confirm_password')

        if password != confirm_password:
            raise ValueError("Las contraseñas no coinciden")
        
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("La contraseña debe contener al menos un carácter especial.")

        return values


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class EventCreate(BaseModel):
    name: str
    description: str
    date: datetime
    location: str

class EventResponse(BaseModel):
    id: int
    name: str
    description: str
    date: datetime
    location: str

    class Config:
        orm_mode = True


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        db_user = User(
            name=user.name,
            surname=user.surname,
            phone=user.phone,
            email=user.email,
            hashed_password=hashed_password.decode('utf-8'),
            created_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error al crear el usuario")



@app.post("/login/")
def login_user(login: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login.username).first()
    if user is None or not bcrypt.checkpw(login.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")
    return {"message": "Inicio de sesión exitoso", "name": user.name}



@app.put("/users/{user_id}/profile-image", response_model=UserResponse)
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    file_location = os.path.join(PROFILE_IMAGE_PATH, f"{user_id}_{file.filename}")
    with open(file_location, "wb") as image_file:
        content = await file.read()
        image_file.write(content)

    user.image = file_location
    db.commit()
    db.refresh(user)
    return user


@app.post("/events/", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    try:
        db_event = Event(
            name=event.name,
            description=event.description,
            date=event.date,
            location=event.location
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear el evento: {e}")

@app.get("/events/{event_id}", response_model=EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a Happenit!"}
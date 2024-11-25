from fastapi import FastAPI, HTTPException, Depends, UploadFile, File ,Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum, DECIMAL ,desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import os
from pydantic import BaseModel, EmailStr, root_validator
from datetime import datetime
from typing import Optional, List
import bcrypt
import re

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

# Modelos de Base de Datos

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
    events = relationship("Event", back_populates="user")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    image_url = Column(String(255), nullable=True)

    user = relationship("User", back_populates="events")



# Pydantic schemas

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
    user_id: int
    title: str
    description: str
    event_date: datetime
    image_url: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    event_date: datetime
    user_id: int
    image_url: Optional[str] = None

    class Config:
        orm_mode = True
        
class EventWithUser(BaseModel):
    id: int
    title: str
    description: str
    event_date: datetime
    user: UserResponse  # Incluye la información del usuario asociada

    class Config:
        orm_mode = True

class EventUpdate(BaseModel):
    title: str
    description: str
    event_date: datetime
    image_url: str

    class Config:
        from_attributes = True

def create_event(db: Session, event: EventCreate, user_id: int):
    db_event = Event(
        user_id=user_id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        image_url=event.image_url,
    )
    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        print(f"Error al crear evento: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")




def get_event_by_id(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Event).offset(skip).limit(limit).all()

def get_events_by_user(db: Session, user_id: int):
    return db.query(Event).filter(Event.user_id == user_id).all()

# Rutas de usuarios

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
    
    return {
        "message": "Inicio de sesión exitoso",
        "user_id": user.id,  # Retornar el user_id
        "name": user.name,
        "token": "some_jwt_token"  # Si usas un token JWT
    }

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


@app.put("/users/{user_id}/profile")
def update_user_profile(
    user_id: int,
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    currentPassword: str = Form(None),
    newPassword: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar los campos del usuario
    user.name = firstName
    user.surname = lastName
    user.email = email

    # Verificar y actualizar la contraseña
    if currentPassword and newPassword:
        if not bcrypt.checkpw(currentPassword.encode('utf-8'), user.hashed_password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
        user.hashed_password = bcrypt.hashpw(newPassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Manejar la carga de una nueva imagen
    if file:
        file_path = f"static/profile_images/{user_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        user.image = file_path

    db.commit()
    db.refresh(user)

    return {"message": "Perfil actualizado exitosamente"}


# Rutas de eventos

@app.post("/events/", response_model=EventResponse)
def create_event_route(event: EventCreate, db: Session = Depends(get_db)):
    try:
        db_event = Event(
            user_id=event.user_id,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            image_url=event.image_url,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        print(f"Error al crear el evento: {e}")
        raise HTTPException(status_code=500, detail="Error al crear el evento")



@app.get("/events/{event_id}", response_model=EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)):
    db_event = get_event_by_id(db, event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return db_event

from sqlalchemy import desc  # Importa la función `desc` para ordenar en orden descendente

@app.get("/events/", response_model=List[EventResponse])
def list_events(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Ordenar por `created_at` en orden descendente para obtener los eventos más recientes
    events = db.query(Event).order_by(desc(Event.created_at)).offset(skip).limit(limit).all()
    return events


@app.get("/users/{user_id}/events/", response_model=List[EventResponse])
def list_user_events(user_id: int, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.user_id == user_id).all()
    return events

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "firstName": user.name,
        "lastName": user.surname,
        "email": user.email,
        "image": user.image
    }

@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    for key, value in event_update.dict(exclude_unset=True).items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event



@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a Happenit!"}
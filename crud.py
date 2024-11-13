from sqlalchemy.orm import Session
from .models import User, Event
from .schemas import UserCreate, EventCreate
import bcrypt

def create_user(db: Session, user: UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_user = User(
        name=user.name,
        surname=user.surname,
        age=user.age,
        phone=user.phone,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_event(db: Session, event: EventCreate):
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

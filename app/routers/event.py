from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas, dependencies

router = APIRouter()

@router.post("/events/", response_model=schemas.EventResponse)
def create_event(event: schemas.EventCreate, db: Session = Depends(dependencies.get_db), user_id: int = Depends(get_user_id)):
    return crud.create_event(db, event, user_id)

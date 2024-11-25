from sqlalchemy.orm import sessionmaker
from .config import engine

def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()

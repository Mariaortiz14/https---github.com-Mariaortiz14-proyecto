from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "mysql+pymysql://root:00000@localhost/happenit"
engine = create_engine(DATABASE_URL, connect_args={"host": "localhost"})
Base = declarative_base()

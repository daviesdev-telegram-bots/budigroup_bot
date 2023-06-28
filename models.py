from sqlalchemy import Float, create_engine, Column, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import dotenv, os
dotenv.load_dotenv()

base = declarative_base()

class User(base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    balance = Column(Float, default=0)

engine = create_engine(os.getenv("DB_URL"))
connection = engine.connect()
base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

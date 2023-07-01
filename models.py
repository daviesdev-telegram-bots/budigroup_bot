from sqlalchemy import Float, create_engine, Column, Boolean, String, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import dotenv, os
dotenv.load_dotenv()

base = declarative_base()

class User(base):
    __tablename__ = "user"
    id = Column(String, primary_key=True)
    is_registered = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=True)
    balance = Column(Float, default=0)
    orders = relationship("Order")

class Order(base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    activation_id = Column(Integer, nullable=True)
    phone_number = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    service = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    type = Column(String)
    user = Column(String, ForeignKey("user.id"))

engine = create_engine(os.getenv("DB_URL"))
connection = engine.connect()
base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

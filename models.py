from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String)
    token = Column(String)
    active = Column(Boolean)

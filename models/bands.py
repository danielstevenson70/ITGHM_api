from .base import Base
from sqlmodel import Field, SQLModel
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String

class Band(Base, table=True):
    __tablename__ = "bands"
    name: str = Field()
    songs: List[str] = Field(sa_column=Column(ARRAY(String)))
from .base import Base
from sqlmodel import Field, SQLModel
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String

class band(Base, table=True):
    __tablename__ = "bands"
    name: str = Field()
    bands: List[str] = Field(sa_column=Column(ARRAY(String)))
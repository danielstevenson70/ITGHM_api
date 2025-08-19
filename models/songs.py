from .base import Base
from sqlmodel import Field, SQLModel
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String

class Songs(Base, table=True):
    __tablename__ = "songs"
    name: str = Field()
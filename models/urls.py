from .base import Base

class Urls(Base, table=True):
    __tablename__ = "urls"

    title: str
    long_url: str
    short_url: str
    user_id: int 
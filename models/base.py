from sqlmodel import Field, SQLModel


class Base(SQLModel):
    id: int = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False
    )
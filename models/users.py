
from sqlmodel import Field, Column, String, UniqueConstraint
from pydantic import EmailStr
import bcrypt
from models.base import Base

class UserBase(Base):
    email: EmailStr = Field(sa_column=Column(String(225), unique=True))
    name: str = Field(sa_column=Column(String(225), nullable=True))

class User(UserBase, table=True):
    __tablename__: str = "users"
    hashed_password: str = Field(sa_column=Column(String))

    UniqueConstraint("email", name="uq_user_email")

    def __repr__(self):
        """
        Returns string representation of model instance
        !r means the value is formatted using its
        __repr__ method rather than its __str__ method.
        """
        return f"<User {self.email!r}>"

    @staticmethod
    def hash_password(password) -> str:
        """
        Transforms password from it's raw textual form to
        cryptographic hashes
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def validate_password(self, pwd) -> bool:
        return bcrypt.checkpw(password=pwd.encode(), hashed_password=self.hashed_password.encode())


class UserSchema(UserBase):
    class Config:
        populate_by_name = True

class UserAccountSchema(Base):
    email: EmailStr
    """ We set an alias for the field so that when this field is serialized or deserialized,
    the name "password" will be used instead of "hashed_password." """
    hashed_password: str = Field(alias="password")

class UserRegistrationSchema(UserAccountSchema):
    name: str

    class Config:
        populate_by_name = True
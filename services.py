from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from models.users import User, UserAccountSchema
from models.tokens import TokenData, is_token_blacklisted
from db import get_session

import config
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# I'm on the fence about seperating these methods into this file
# There's a case to be made that they could also work in the model as static methods?

def create_user(user: UserAccountSchema, session: Session):
    db_user = User(**user.dict())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user(email: str, session: Session):
    statement = select(User).where(User.email == email)
    return session.exec(statement).one()


async def get_current_user_token(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if config.ALGORITHM is None:
          raise ValueError("ALGORITHM configuration is required")

        payload = jwt.decode(token, config.SECRET_KEY,
                             algorithms=[config.ALGORITHM])
        email: str | None = payload.get("email")

        if not email or is_token_blacklisted(token, session):
            raise credentials_exception


        token_data = TokenData(email=email)
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.DecodeError:
        raise credentials_exception

    statement = select(User).where(User.email == email)
    user = session.exec(statement).one()
    if user is None:
        raise credentials_exception
    return token_data

import uvicorn

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from db import get_session

from models.urls import Urls
from models.users import User, UserRegistrationSchema, UserSchema, UserAccountSchema
from models.tokens import Token, BlacklistedToken, create_access_token

import config

from services import get_current_user_token, create_user, get_user

from ytmusicapi import YTMusic

ytmusic = YTMusic()

# Import or initialize metallum here
# Example: from metallumapi import Metallum
# metallum = Metallum()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Garden of Heavy and Metal!"}


@app.post('/register', response_model=UserSchema)
def register_user(payload: UserRegistrationSchema, session: Session = Depends(get_session)):
    """Processes request to register user account."""
    payload.hashed_password = User.hash_password(payload.hashed_password)
    return create_user(user=payload, session=session)


@app.post('/login', status_code=200)
async def login(payload: UserAccountSchema, session: Session = Depends(get_session)):
    try:
        user: User = get_user(email=payload.email, session=session)
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials"
        )

    is_validated: bool = user.validate_password(payload.hashed_password)
    print(f"Is user validated? {is_validated}")
    if not is_validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials"
        )

    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get('/getUser', status_code=200)
async def get_user_id(current_user: User = Depends(get_current_user_token)):
    return {"email": current_user.email, "id": current_user.id}

@app.get('/artists')
async def artists(search_artist: str):
    artist_result = ytmusic.search(search_artist)
    artist_id = artist_result[0].get('artists')[0].get('id')
    artists_results = ytmusic.get_artist  # Replace with actual implementation
    return artists_results


@app.get('/songs')
async def songs(search_artist_string: str):
    artist_result = ytmusic.search(search_artist_string)
    artist_id = artist_result[0].get('artists')[0].get('id')
    song_results = ytmusic.get_artist(artist_id)  # Replace with actual implementation
    return song_results  # to populate more of the page if needed

# OR grab the thumbnails
# ...
# get thumbnails

# @app.get('/genre')
# async def genre(search_artist_genre: str):
#     artist_result = metallum.search(search_artist_genre)
#     genre_id = artist_result[0].get('genre').get('artists')[0].get('id')
#     genre_results = metallum.get_genre
#     return genre_results

# @app.get('/tourdates')
# async def tourdates(search_artist_tourdates: str):
#     artist_result = 
#     artist_id = 
#     tourdates_results =
#     return tourdates

@app.get('/randomband')
async def randomband():
    artist_result = ytmusic(randomband)
    artist = artist_result[0].get('artist')[0].get('id')
    randomband_results = ytmusic.get_artist
    return randomband_results


@app.post('/logout')
def logout(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        blacklisted_token = BlacklistedToken(
            created_at=datetime.now(timezone.utc), token=token)
        session.add(blacklisted_token)
        session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"details": "Logged out"}


if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)


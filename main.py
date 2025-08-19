from re import search
import metallum
import uvicorn

from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
from db import get_session

from models.bands import band
from models.genres import Genres
from models.users import User, UserRegistrationSchema, UserSchema, UserAccountSchema
from models.tokens import Token, BlacklistedToken, create_access_token

import os
import config
import requests
from dotenv import load_dotenv

from services import get_current_user_token, create_user, get_user

from ytmusicapi import YTMusic

ytmusic = YTMusic()
youtube_router = APIRouter(prefix="/youtube")


# Import or initialize metallum here
# Example: from metallumapi import Metallum
# metallum = Metallum()

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    print("anything")
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


@app.get('/bands')
async def band_name(search: str, session: Session = Depends(get_session)):
    statement = select(band_name).where(func.lower(band_name) == search.lower())
    bands = session.exec(statement).all()
    return band_name


@app.get('/genre')
async def genres(searched_genre: str, session: Session = Depends(get_session)):
    statement = select(Genres).where(func.lower(Genres.name) == searched_genre.lower())
    bands = session.exec(statement).all()
    return bands


@app.get("/songs")
async def songs(search_artist_string: str):
    # Search for the artist or songs
    search_results = ytmusic.search(search_artist_string, filter="songs")
    
    thumbnail_list = []
    for song in search_results:
        thumbnails = song.get("thumbnails")
        if thumbnails:
            # Grab the last (largest) thumbnail
            thumbnail_list.append(thumbnails[-1])
    
    return thumbnail_list



# @app.get('/tourdates')
# async def tourdates(search_artist_tourdates: str):
#     artist_result = 
#     artist_id = 
#     tourdates_results =
#     return tourdates

@app.get('/randomband')
async def randomband():
    artist_result = ytmusic(randomband)
    artist_result = artist_result[0].get('artist')[0].get('id')
    randomband_results = ytmusic.get_artist_
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

@app.post("/generate")
async def generate(request: Request):
    body = await request.json()
    prompt = body.get("prompt")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    data = response.json()
    return {"output": data["choices"][0]["message"]["content"]}

if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)


from calendar import day_name
from re import search
import uvicorn

from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
from db import get_session

from models.songs import Songs
from models.bands import Band
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

# origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get('/bands/{search_bands}')
async def band_name(search_bands: str, session: Session = Depends(get_session)):
    statement = select(Band).where(func.lower(Band.band_name) == search_bands.lower())
    band_info = session.exec(statement).one_or_none()
    song_id_array = band_info.song_id
    complete_song_array = []
    for song_id in song_id_array:
        statement = select(Songs).where(Songs.id == song_id)
        song_name = session.exec(statement).one_or_none()
        complete_song_array.append(song_name)
        try:
            search_results = ytmusic.search(query=search_bands, filter='songs')
            youtube_links = []
            for result in search_results:
                if result['resultType'] == 'song':
                    band_id = result['videoId']
                    youtube_links.append(f'https://www.youtube.com/embed/{band_id}')
        except Exception as e:
            youtube_links = []
    return {"name": band_info.band_name, "songs": complete_song_array}


@app.get('/genre/{search_genre}')
async def genres(search_genre: int, session: Session = Depends(get_session)):
    statement = select(Genres).where(Genres.id == search_genre)  
    genre_info = session.exec(statement).one_or_none()
    band_id_array = genre_info.Bands
    complete_band_array = []
    for band_id in band_id_array:
        statement = select(Band).where(Band.id == band_id)
        band_array = session.exec(statement).one()
        complete_band_array.append(band_array)
    return {"name": genre_info.name, "bands": complete_band_array}


# @app.get("/songs")
# async def songs(search_artist_string: str):



# @app.get('/tourdates')
# async def tourdates(search_artist_tourdates: str):
#     artist_result = 
#     artist_id = 
#     tourdates_results =
#     return tourdates

# @app.get('/randomband')
# async def randomband():
#     artist_result = ytmusic(randomband)
#     artist_result = artist_result[0].get('artist')[0].get('id')
#     randomband_results = ytmusic.get_artist_
#     return randomband_results


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

# @app.post("/generate")
# async def generate(request: Request):
#     body = await request.json()
#     prompt = body.get("prompt")

#     response = requests.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {OPENAI_API_KEY}",
#             "Content-Type": "application/json"
#         },
#         json={
#             "model": "gpt-4o-mini",
#             "messages": [{"role": "user", "content": prompt}]
#         }
#     )

    data = response.json()
    return {"output": data["choices"][0]["message"]["content"]}

if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)


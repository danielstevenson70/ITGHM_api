from re import search
import psycopg2
from psycopg2.extras import RealDictCursor
import metallum
import uvicorn

from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from db import get_session

from models.urls import Urls
from models.users import User, UserRegistrationSchema, UserSchema, UserAccountSchema
from models.tokens import Token, BlacklistedToken, create_access_token

import os
import config
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

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

class ArtistQuery(BaseModel):
    search_artist: str

@app.get('/genre')
async def genre(searched_genre: str):
    print('\ntest 123\n')
    # artist_result = ytmusic.search(searched_artists)
    # artist_id = artist_result[0].get('artists')[0].get('id')
    # artists_results = ytmusic.get_videos(artist_id)  # Replace with actual implementation
    # return { "artist": artists_results }


    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'  # Supabase requires SSL
    )

    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("""
    select
        band_id as id,
        band_name as name
    from
        bands
    join lateral (
        select
        name,
        UNNEST("Bands") as band_id
        from
        genre
    ) as genre_band_ids on genre_band_ids.band_id = bands.id
    where
        genre_band_ids.name = %s
    """, (searched_genre))
    cur.execute("""
    select
        band_id as id,
        band_name as name
    from
        bands
    join lateral (
        select
        name,
        UNNEST("Bands") as band_id
        from
        genre
    ) as genre_band_ids on genre_band_ids.band_id = bands.id
    where
        genre_band_ids.name = %s
    """, (searched_genre,))
    bands = cur.fetchall()
    return bands


@app.get('/songs')
async def songs(search_artist_string: str):
    artist_result = ytmusic.search(search_artist_string)
    artist_id = artist_result[0].get('artists')[0].get('id')
    song_results = song_results.get('thumbnail_list')
    thumbnail_list = []
    for song in song_result.get('songs', {}).get('results'):
        if not song.get('thumbnails'):
            continue
        thumbnail_list.append(song.get('thumbnails')[-1])
    return thumbnail_list

# return(
#     {
#         "url": "https://lh3.googleusercontent.com/cfc1cp85SvWi0PYmiOL4KWSz1WF1ZBN4hGfUQugVSsMvmoz8-i2wzYm6Z8-CnJRBDff3vOMj95apta8H=w60-h60-l90-rj",
#         "width": 60,
#         "height": 60
#     },
# )
# OR grab the thumbnails
# ...
# get thumbnails

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


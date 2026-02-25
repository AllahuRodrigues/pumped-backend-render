from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging

from api.routes import router as api_router
from api.db import router as db_router
from api.ab import router as ab_router
from api.events import router as events_router
from api.experiments import router as experiments_router
from api.posts import router as posts_router
from api.gyms import router as gyms_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# API routes
app.include_router(api_router)
app.include_router(db_router)
app.include_router(ab_router)
app.include_router(events_router)
app.include_router(experiments_router)
app.include_router(posts_router)
app.include_router(gyms_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI! This app is Live!"}

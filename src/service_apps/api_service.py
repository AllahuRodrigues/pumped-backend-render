from fastapi import FastAPI

from api.db import router as db_router
from api.gyms import router as gyms_router
from api.posts import router as posts_router
from api.routes import router as base_router


app = FastAPI(title="pumped-api-service")
app.include_router(base_router)
app.include_router(db_router)
app.include_router(posts_router)
app.include_router(gyms_router)


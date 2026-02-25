from fastapi import FastAPI

from api.ab import router as ab_router
from api.db import router as db_router
from api.events import router as events_router
from api.experiments import router as experiments_router
from api.routes import router as base_router


app = FastAPI(title="pumped-analytics-service")
app.include_router(base_router)
app.include_router(db_router)
app.include_router(ab_router)
app.include_router(events_router)
app.include_router(experiments_router)


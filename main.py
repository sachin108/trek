from fastapi import FastAPI

from src.database import engine
from src.models import Base
from src.routers import auth

Base.metadata.create_all(bind=engine)

app=FastAPI(title="paper trading app")

app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "paper trading app is up"}
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.routers import auth, stocks, orders, portfolio

# Base.metadata.create_all(bind=engine) - no need of this if we are using alembic to track and apply DB changes

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app=FastAPI(title="paper trading app")

app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(orders.router)
app.include_router(portfolio.router)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file))
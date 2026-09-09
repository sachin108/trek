from fastapi import FastAPI
from src.routers import auth, stocks, orders

# Base.metadata.create_all(bind=engine) - no need of this if we are using alembic to track and apply DB changes

app=FastAPI(title="paper trading app")

app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(orders.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "paper trading app is up"}
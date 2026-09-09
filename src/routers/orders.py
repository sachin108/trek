from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user
from src.models import User
from src.schemas import OrderCreate, OrderResponse
from src.services.trading import execute_market_order

router = APIRouter(prefix="/orders", tags=["Orders & Trading"])

@router.post("", response_model=OrderResponse ,status_code=status.HTTP_201_CREATED)
async def place_order(order: OrderCreate,
                      current_user: Annotated[User, Depends(get_current_user)],
                      db: Annotated[Session, Depends(get_db)]):
    return await execute_market_order(user_id=current_user.id, order=order, db=db)
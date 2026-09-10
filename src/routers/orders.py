from typing import Annotated, Optional

from fastapi import APIRouter, status
from fastapi.params import Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_user
from src.models import User, OrderSide, OrderStatus, Order
from src.schemas import OrderCreate, OrderResponse, OrderHistoryResponse
from src.services.trading import execute_market_order

router = APIRouter(prefix="/orders", tags=["Orders & Trading"])

@router.post("/", response_model=OrderResponse ,status_code=status.HTTP_201_CREATED)
async def place_order(order: OrderCreate,
                      current_user: Annotated[User, Depends(get_current_user)],
                      db: Annotated[Session, Depends(get_db)]):
    return await execute_market_order(user_id=current_user.id, order=order, db=db)

@router.get("", response_model=OrderHistoryResponse)
@router.get("/", response_model=OrderHistoryResponse, include_in_schema=False)
def get_order_history(current_user: Annotated[User, Depends(get_current_user)],
                      db: Annotated[Session, Depends(get_db)],
                      symbol : Optional[str] = Query(default=None),
                      order_side : Optional[OrderSide] = Query(default=None) ,
                      status : Optional[OrderStatus] = Query(default=None),
                      page : int = Query(1, ge=1),
                      page_size: int = Query(10, ge=1, le=50),
                      ):
    base_query=select(Order).where(Order.user_id == current_user.id)
    if symbol and symbol.strip():
        base_query = base_query.where(Order.symbol == symbol.strip().upper())

    if order_side and order_side.strip():
        base_query = base_query.where(Order.order_side == order_side.strip().upper())

    if status and status.strip():
        base_query = base_query.where(Order.status == status.strip().upper())

    count=select(func.count()).select_from(base_query.subquery())
    total_rows=db.scalar(count) or 0

    offset = (page - 1) * page_size
    query=(
        base_query.order_by(Order.created_at.desc()).limit(page_size).offset(offset)
    )
    items=db.scalars(query).all()

    total_pages=(total_rows + page_size -1) // page_size if total_rows > 0 else 1

    return OrderHistoryResponse(items=items,
                                total=total_rows,
                                page=page,
                                page_size=page_size,
                                total_pages=total_pages)

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import User, Holding, Order, OrderStatus, OrderExecutionType
from src.schemas import OrderCreate
from src.services.market_data import get_stock_quote


async def execute_market_order(user_id:int, order:OrderCreate, db:Session) -> Order :
    stock_name = order.symbol.strip().upper()

    # fetch live price
    quote = await get_stock_quote(stock_name)

    if not quote or quote.current_price <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unable to retrieve market price for symbol '{stock_name}'")

    execution_price = quote.current_price
    total_cost = (execution_price * order.quantity)

    # lock the user's row to avoid concurrent balance race conditions
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # retrieve any existing holding for this symbol
    holding = db.scalar(select(Holding).where(
            Holding.user_id == user_id, Holding.symbol == stock_name).with_for_update())

    # process BUY
    if order.order_type.upper() == "BUY":
        if user.available_funds < total_cost:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Insufficient funds. Required: ${total_cost}, Available: ${user.available_funds}")

        user.available_funds = user.available_funds - total_cost

        if holding:
            existing_total_cost = holding.quantity * holding.average_price
            new_quantity = holding.quantity + order.quantity
            new_avg_price = (existing_total_cost + total_cost) / new_quantity

            holding.quantity = new_quantity
            holding.average_price = new_avg_price

        else:
            new_holding = Holding(
                user_id=user.id,
                symbol=stock_name,
                quantity=order.quantity,
                average_price=execution_price,
                exchange=order.stock_exchange,
            )
            db.add(new_holding)

    # process SELL
    elif order.order_type.upper() == "SELL":
        if not holding or holding.quantity < order.quantity:
            current_quantity = holding.quantity
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient shares. Trying to sell: {order.quantity}, Owned: {current_quantity}",
            )

        user.available_funds = user.available_funds + total_cost

        if holding.quantity == order.quantity:
            db.delete(holding)
        else:
            holding.quantity = holding.quantity - order.quantity

    order_record = Order(
        user_id=user.id,
        symbol=stock_name,
        order_type=order.order_type,
        status=OrderStatus.COMPLETED,
        execution_type=OrderExecutionType.MARKET,
        stock_exchange=order.stock_exchange,
        quantity=order.quantity,
        execution_price=execution_price,
        total_amount=total_cost,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(order_record)

    db.commit()
    db.refresh(order_record)
    return order_record

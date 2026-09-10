import asyncio
from decimal import Decimal
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import User, Holding
from src.schemas import PortfolioSummaryResponse, HoldingResponse
from src.services.market_data import get_stock_quote


async def get_user_portfolio(user:User, db:Session) -> PortfolioSummaryResponse:
    # fetch all holdings of user
    holdings = db.scalars(
        select(Holding).where(Holding.user_id == user.id),
    ).all()

    if not holdings:
        return PortfolioSummaryResponse(
            available_funds=user.available_funds,
            total_market_value=Decimal("0.00"),
            total_portfolio_value=user.available_funds,
            total_unrealized_pnl=Decimal("0.00"),
            holdings=[]
        )

    # concurrently fetch quote for all held symbols
    tasks=[get_stock_quote(h.symbol) for h in holdings]
    quotes=await asyncio.gather(*tasks, return_exceptions=True)

    holdings_response : List[HoldingResponse] = []
    total_market_value = Decimal("0.00")
    total_cost_basis = Decimal("0.00")

    # calculate metrics per holding
    for holding, quote in zip(holdings, quotes):
        if quote and not isinstance(quote, Exception) and quote.current_price:
            current_price=quote.current_price
        else:
            current_price=holding.average_price

        total_cost = (holding.quantity * holding.average_price)
        market_val = (holding.quantity * current_price)
        unrealized_pnl = market_val - total_cost

        if total_cost > 0:
            unrealized_pnl_pct = ((unrealized_pnl / total_cost) * Decimal("100"))
        else:
            unrealized_pnl_pct = Decimal("0.00")

        total_market_value+=market_val
        total_cost_basis+=total_cost

        holdings_response .append(HoldingResponse(
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_price=holding.average_price,
            current_price=current_price,
            market_value=market_val,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percentage=unrealized_pnl_pct,
        ))

    total_unrealized_pnl = total_market_value-total_cost_basis
    total_portfolio_value = user.available_funds + total_market_value

    return PortfolioSummaryResponse(
        available_funds=Decimal(user.available_funds),
        total_market_value=total_market_value,
        total_portfolio_value=total_portfolio_value,
        total_unrealized_pnl=total_unrealized_pnl,
        holdings=holdings_response,
    )
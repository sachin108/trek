from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from sqlalchemy.orm import DeclarativeBase

from trek.models import OrderType, OrderExecutionType, OrderStatus


# ------- User & Auth ------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=5, max_length=50)
    password: str = Field(..., min_length=12)
    email: EmailStr

class UserProfileResponse(BaseModel):
    id : int
    username : str
    available_funds : Decimal
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

# ------- Stock search and Quote ------
class StockSearchResults(BaseModel):
    symbol: str
    name: str
    exchange: str

class StockQuote(BaseModel):
    symbol: str
    current_price: Decimal
    change: Decimal
    percent_change: Decimal
    high_24h: Optional[Decimal]=None
    low_24h: Optional[Decimal]=None
    volume:Optional[int]=None

# Portfolio and holdings
class HoldingResponse(BaseModel):
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_percentage: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)

class PortfolioSummaryResponse(BaseModel):
    available_funds: Decimal
    total_market_value: Decimal
    total_portfolio_value: Decimal # available_funds + total_market_value
    total_unrealized_pnl: Decimal
    holdings: List[HoldingResponse]

# Orders (buy / sell)
class OrderCreate(BaseModel):
    symbol: str
    order_type: OrderType
    execution_type: OrderExecutionType = OrderExecutionType.MARKET
    quantity: Decimal = Field(..., gt=0)
    stock_exchange: str
    limit_price: Optional[Decimal] = Field(..., gt=0)

class OrderResponse(BaseModel):
    order_id: int
    symbol: str
    order_type: OrderType
    execution_type: OrderExecutionType
    status: OrderStatus
    quantity: Decimal
    execution_price: Optional[Decimal]
    limit_price: Optional[Decimal]
    total_amount: Optional[Decimal]
    created_at: datetime
    filled_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)




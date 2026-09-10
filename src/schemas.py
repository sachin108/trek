from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Union

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, ValidationError
from pydantic_core import PydanticCustomError

from .models import OrderSide, OrderType, OrderStatus

# ------- User & Auth ------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=5, max_length=50)
    # ellipsis (...) are placeholder indicating that a field is required and has no default value,
    # even when you are adding validation rules or metadata via Field()

    password: str
    email: EmailStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, password:str):
        if len(password) < 12:
            raise PydanticCustomError("string_too_short","Password must be at least 12 characters")
        return password


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
class StockSearchResult(BaseModel):
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
    average_price: Decimal
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
    side: OrderSide = Field(..., alias="order_side")
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Field(..., gt=0)
    stock_exchange: str = "NASDAQ"
    limit_price: Optional[Decimal] = Field(gt=0, default=None)
    model_config = {
            "populate_by_name": True  # Allows accepting both 'side' and 'order_side'
        }

class OrderResponse(BaseModel):
    id: int
    symbol: str
    order_side: OrderSide
    order_type: OrderType
    status: OrderStatus
    quantity: Decimal
    execution_price: Optional[Decimal]
    limit_price: Optional[Decimal]
    total_amount: Optional[Decimal]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
    '''
    field names must match in Pydantic Schema and models if from_attributes=True,
    bcz it reads data using Python's getattr(orm_object, field_name). If ORM model 
    has id and Pydantic schema expects order_id, Pydantic looks for orm_obj.order_id, 
    fails to find it, and raises a ResponseValidationError.    
    
    or 
    
    class OrderResponse(BaseModel):
        order_id: int = Field(validation_alias="id")  # Reads 'id' from SQLAlchemy model
    
        model_config = ConfigDict(
            from_attributes=True,
            populate_by_name=True,  # Allows using 'order_id' or 'id' during manual init
        )
    '''

class CandleStickBar(BaseModel):
    time : Union[int, str]
    open_price : Decimal
    high_price : Decimal
    low_price : Decimal
    close_price : Decimal
    volume : Optional[int] = None


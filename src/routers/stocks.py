from typing import Annotated, List

from fastapi import APIRouter
from fastapi.params import Query, Depends

from src.dependencies import get_current_user
from src.models import User
from src.schemas import StockSearchResult
from src.services.market_data import search_stocks

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])

@router.get("/search", response_model=List[StockSearchResult])
async def search(
        q:Annotated[str, Query(min_length=1)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    results = await search_stocks(stock_name=q)
    return results
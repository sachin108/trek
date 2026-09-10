from typing import Annotated, List

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Query, Depends

from src.dependencies import get_current_user
from src.models import User
from src.schemas import StockSearchResult, StockQuote, CandleStickBar
from src.services.market_data import search_stocks, get_stock_quote, get_stock_history

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])

@router.get("/search", response_model=List[StockSearchResult])
async def search(
        q:Annotated[str, Query(min_length=1)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    results = await search_stocks(stock_name=q)
    return results

@router.get("/{symbol}/quote", response_model=StockQuote)
async def get_quote(symbol:str, current_user: Annotated[User, Depends(get_current_user)]):
    stock_data= await get_stock_quote(symbol)
    if not stock_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Quote not found for ticker '{symbol.upper()}'. Make sure the symbol is valid.",)
    return stock_data

@router.get("/{symbol}/history", response_model=List[CandleStickBar])
async def stock_history(
                symbol:str,
                current_user: Annotated[User, Depends(get_current_user)],
                period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|5y|max)$"),
                interval: str = Query("1d", regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo)$"),
        ) :
    bars = await get_stock_history(symbol.strip().upper(), period, interval)

    if not bars:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No historical chart data available for '{symbol.upper()}'",
                        )
    return bars

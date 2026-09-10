from typing import Annotated, List

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Query, Depends

from src.dependencies import get_current_user
from src.models import User
from src.schemas import StockSearchResult, StockQuote
from src.services.market_data import search_stocks, get_stock_quote

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
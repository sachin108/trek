from typing import List

import httpx
import yfinance

from src.schemas import StockSearchResult


async  def search_stocks(stock_name:str) -> List[StockSearchResult]:
    stock_name = stock_name.strip()
    if not stock_name:
        return []
    try:
        search_engine = yfinance.Search(stock_name, max_results=3)
        quotes = search_engine.quotes
        print(f"quotes {quotes}")
    except Exception as e:
        print(f" error in search_stocks: {e}")
        return []

    results : List[StockSearchResult] = []
    for item in quotes:
        quote_type = item.get('quoteType', "")
        if quote_type in ['EQUITY', 'ETF']:
            results.append(StockSearchResult(
                symbol=item.get('symbol', "").upper(),
                name=item.get('shortname', "") or item.get('longname', "") or item.get('symbol', ""),
                exchange=item.get('exchange', "")
            ))

    return results

async def get_stock_quote(stock_name:str) -> StockSearchResult:
    pass
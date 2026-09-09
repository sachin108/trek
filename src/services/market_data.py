from typing import List

import httpx

from src.schemas import StockSearchResult


async  def search_stocks(stock_name:str) -> List[StockSearchResult]:
    stock_name = stock_name.strip()
    if not stock_name:
        return []

    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        "q": stock_name,
        "quotesCount": 10,
        "newsCount": 0,
        "listsCount": 0,
        "enableFuzzyQuery": False,
    }
    headers = {"User-Agent": "Mozilla/5.0 (FastAPI-PaperTrading/1.0)"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                return []
            data=response.json()
    except Exception as e:
        print(f" error in search_stocks: {e}")
        return []

    results : List[StockSearchResult] = []
    for item in data.get('quotes', []):
        quote_type = item.get('quoteType', "")
        if quote_type not in ['EQUITY', 'ETF']:
            results.append(StockSearchResult(
                symbol=item.get('symbol', "").upper(),
                name=item.get('shortname', "") or item.get('longname', "") or item.get('symbol', ""),
                exchange=item.get('exchange', "")
            ))

    return results


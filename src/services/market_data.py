import time
from decimal import Decimal
from typing import List, Dict, Optional
import yfinance
from starlette.concurrency import run_in_threadpool

from src.schemas import StockSearchResult, StockQuote, CandleStickBar

# in memory cache
_quote_cache : Dict[str, tuple[float, StockQuote]] = {}
CACHE_TTL_SECONDS = 15

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

def _fetch_quote_sync(symbol:str):
    symbol = symbol.strip().upper()
    ticker=yfinance.Ticker(symbol)
    info=ticker.fast_info
    try:
        current_price = info.last_price or None
        if current_price is None:
            return None

        if current_price is None or current_price <=0:
            history=ticker.history(period="1d")
            if not history.empty and "Close" in history:
                current_price = float(history["Close"].iloc[-1])

        if current_price is None or current_price <= 0:
            return None

        previous_close = info.previous_close or None
        if previous_close is None or previous_close <= 0:
            previous_close = current_price

        change = current_price - previous_close
        percent_change = change / previous_close * 100

        return StockQuote(
            symbol=symbol,
            current_price=Decimal(str(round(current_price, 2))),
            change=Decimal(str(round(change, 2))),
            percent_change=Decimal(str(round(percent_change, 2))),
            high_24h=Decimal(str(round(info.day_high, 2))) if info.day_high else None,
            low_24h=Decimal(str(round(info.day_low, 2))) if info.day_low else None,
            volume=int(info.last_volume) if info.last_volume else None,
        )
    except Exception as e:
        print(f" error in _fetch_quote_sync: {e}")
        return None


async def get_stock_quote(stock_name:str) -> Optional[StockQuote]:
    now=time.time()
    if stock_name in _quote_cache:
        cached_time, cached_quote = _quote_cache[stock_name]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_quote

    quote = await run_in_threadpool(_fetch_quote_sync, stock_name)
    if quote:
        _quote_cache[stock_name] = (now, quote)

    return quote


def _fetch_history_sync(
    symbol: str, period: str = "1mo", interval: str = "1d"
) -> List[dict]:
    ticker = yfinance.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        return []

    bars = []
    is_intraday = interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h")

    for idx, row in df.iterrows():
        # Intraday requires integer seconds; Daily/Weekly requires "YYYY-MM-DD"
        time_val = int(idx.timestamp()) if is_intraday else idx.strftime("%Y-%m-%d")

        bars.append(
            {
                "time": time_val,
                "open_price": round(float(row["Open"]), 2),
                "high_price": round(float(row["High"]), 2),
                "low_price": round(float(row["Low"]), 2),
                "close_price": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if "Volume" in row else 0,
            }
        )
    return bars

async def get_stock_history(stock_name:str, period:str="1mo", interval:str="1d") -> List[CandleStickBar]:
    return await run_in_threadpool(_fetch_history_sync, stock_name, period, interval)
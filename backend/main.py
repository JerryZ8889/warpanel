import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from data_fetcher import fetch_market_data, fetch_history
from polymarket import fetch_ceasefire_predictions
from analyzer import analyze
from database import save_snapshot, get_latest_snapshot, get_history as get_db_history

app = FastAPI(title="美伊局势看板")

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/refresh")
async def refresh():
    """Fetch all data, save snapshot, and return results."""
    # Run market data fetch in a thread (yfinance is synchronous)
    loop = asyncio.get_event_loop()
    market_data = await loop.run_in_executor(None, fetch_market_data)

    # Fetch Polymarket data
    polymarket = await fetch_ceasefire_predictions()

    # Analyze
    analysis = analyze(market_data, polymarket)

    snapshot = {
        "indicators": market_data,
        "polymarket": polymarket,
        "analysis": analysis,
    }

    # Save to database
    save_snapshot(snapshot)

    return JSONResponse(content=snapshot)


@app.get("/api/latest")
async def latest():
    """Return the most recent cached snapshot."""
    snap = get_latest_snapshot()
    if snap:
        return JSONResponse(content=snap)
    return JSONResponse(content={"error": "No data yet. Click refresh."}, status_code=404)


@app.get("/api/history/{symbol}")
async def history(symbol: str, period: str = "1mo"):
    """Return historical price data for a symbol."""
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_history, symbol, period)
    return JSONResponse(content=data)


@app.get("/api/snapshots")
async def snapshots(limit: int = 50):
    """Return historical snapshots for trend analysis."""
    data = get_db_history(limit)
    return JSONResponse(content=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

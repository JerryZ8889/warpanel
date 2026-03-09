"""Local development entry point. All modules live in api/ directory."""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from data_fetcher import fetch_market_data, fetch_batch, fetch_history, BATCHES
from polymarket import fetch_ceasefire_predictions
from analyzer import analyze
from database import save_snapshot, get_latest_snapshot, get_history as get_db_history

CACHE_TTL = 5 * 60
BJT = timezone(timedelta(hours=8))

app = FastAPI(title="美伊局势看板")

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "public")


@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def _check_cache():
    """Return (snapshot, age_seconds) if cache is valid, else (None, None)."""
    snap = get_latest_snapshot()
    if snap and snap.get("timestamp"):
        try:
            cached_time = datetime.strptime(snap["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=BJT)
            age = (datetime.now(BJT) - cached_time).total_seconds()
            if age < CACHE_TTL and snap.get("data"):
                return snap, int(age)
        except Exception:
            pass
    return None, None


@app.get("/api/batch/{batch_id}")
async def batch(batch_id: int):
    if batch_id < 1 or batch_id > 5:
        return JSONResponse(content={"error": "batch_id must be 1-5"}, status_code=400)
    snap, age = _check_cache()
    if snap:
        keys = BATCHES.get(batch_id, [])
        cached = snap["data"].get("indicators", {})
        batch_data = {k: cached[k] for k in keys if k in cached}
        if batch_data:
            return JSONResponse(content=batch_data, headers={"X-Cache": "HIT", "X-Cache-Age": str(age)})
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_batch, batch_id)
    return JSONResponse(content=data, headers={"X-Cache": "MISS"})


@app.get("/api/polymarket")
async def polymarket():
    snap, age = _check_cache()
    if snap and snap["data"].get("polymarket"):
        return JSONResponse(content=snap["data"]["polymarket"], headers={"X-Cache": "HIT", "X-Cache-Age": str(age)})
    data = await fetch_ceasefire_predictions()
    return JSONResponse(content=data, headers={"X-Cache": "MISS"})


@app.post("/api/analyze")
async def analyze_post(request: Request):
    body = await request.json()
    indicators = body.get("indicators", {})
    polymarket_data = body.get("polymarket", [])
    analysis = analyze(indicators, polymarket_data)
    snapshot = {
        "indicators": indicators,
        "polymarket": polymarket_data,
        "analysis": analysis,
    }
    save_snapshot(snapshot)
    return JSONResponse(content={"analysis": analysis})


@app.get("/api/refresh")
async def refresh():
    loop = asyncio.get_event_loop()
    market_data = await loop.run_in_executor(None, fetch_market_data)
    polymarket_data = await fetch_ceasefire_predictions()
    analysis = analyze(market_data, polymarket_data)
    snapshot = {
        "indicators": market_data,
        "polymarket": polymarket_data,
        "analysis": analysis,
    }
    save_snapshot(snapshot)
    return JSONResponse(content=snapshot)


@app.get("/api/latest")
async def latest():
    snap = get_latest_snapshot()
    if snap:
        return JSONResponse(content=snap)
    return JSONResponse(content={"error": "No data yet. Click refresh."}, status_code=404)


@app.get("/api/history/{symbol}")
async def history(symbol: str, period: str = "1mo"):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_history, symbol, period)
    return JSONResponse(content=data)


@app.get("/api/snapshots")
async def snapshots(limit: int = 50):
    data = get_db_history(limit)
    return JSONResponse(content=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""Local development entry point. All modules live in api/ directory."""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from data_fetcher import fetch_batch, fetch_history_batch, fetch_ec_futures, BATCHES, HISTORY_BATCHES
from polymarket import fetch_ceasefire_predictions
from analyzer import analyze
from database import save_snapshot, get_latest_snapshot

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
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, fetch_batch, batch_id)
    return JSONResponse(content=data, headers={"X-Cache": "MISS"})


@app.get("/api/polymarket")
async def polymarket():
    snap, age = _check_cache()
    if snap and snap["data"].get("polymarket"):
        return JSONResponse(content=snap["data"]["polymarket"], headers={"X-Cache": "HIT", "X-Cache-Age": str(age)})
    data = await fetch_ceasefire_predictions()
    return JSONResponse(content=data, headers={"X-Cache": "MISS"})


@app.get("/api/ec")
async def ec_futures():
    """Fetch EC futures data, with 5-min cache."""
    snap, age = _check_cache()
    if snap and snap["data"].get("ec"):
        return JSONResponse(content=snap["data"]["ec"], headers={"X-Cache": "HIT", "X-Cache-Age": str(age)})
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, fetch_ec_futures)
    return JSONResponse(content=data, headers={"X-Cache": "MISS"})


@app.post("/api/analyze")
async def analyze_post(request: Request):
    body = await request.json()
    indicators = body.get("indicators", {})
    polymarket_data = body.get("polymarket", [])
    ec_data = body.get("ec")
    analysis = analyze(indicators, polymarket_data)
    snapshot = {
        "indicators": indicators,
        "polymarket": polymarket_data,
        "analysis": analysis,
    }
    if ec_data:
        snapshot["ec"] = ec_data
    save_snapshot(snapshot)
    return JSONResponse(content={"analysis": analysis})


@app.get("/api/latest")
async def latest():
    snap = get_latest_snapshot()
    if snap and snap.get("timestamp"):
        try:
            cached_time = datetime.strptime(snap["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=BJT)
            age = (datetime.now(BJT) - cached_time).total_seconds()
            if age < CACHE_TTL:
                return JSONResponse(content=snap)
        except Exception:
            pass
    return JSONResponse(content={"expired": True})


@app.get("/api/history-batch/{batch_id}")
async def history_batch(batch_id: int, period: str = "1mo"):
    if batch_id < 1 or batch_id > 3:
        return JSONResponse(content={"error": "batch_id must be 1-3"}, status_code=400)
    keys = HISTORY_BATCHES.get(batch_id, [])
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, fetch_history_batch, keys, period)
    return JSONResponse(content=data)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

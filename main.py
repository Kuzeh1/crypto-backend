# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time

app = FastAPI(title="Crypto Tracker API")

# Allow frontend to call backend during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COINGECKO = "https://api.coingecko.com/api/v3"

# --- Simple in-memory cache ---
CACHE = {}
CACHE_TTL = 60  # seconds

def cache_get(key: str):
    item = CACHE.get(key)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > CACHE_TTL:
        del CACHE[key]
        return None
    return data

def cache_set(key: str, data):
    CACHE[key] = (time.time(), data)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/prices")
async def prices(ids: str = "bitcoin,ethereum", vs_currency: str = "usd", include_24hr_change: bool = True):
    """
    Example: /api/prices?ids=bitcoin,ethereum&vs_currency=usd&include_24hr_change=true
    """
    key = f"prices:{ids}:{vs_currency}:{include_24hr_change}"
    cached = cache_get(key)
    if cached:
        return cached

    params = {
        "ids": ids,
        "vs_currencies": vs_currency,
        "include_24hr_change": str(include_24hr_change).lower()
    }

    async with httpx.AsyncClient(
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0 (compatible; CryptoTracker/1.0)"}
    ) as client:
        r = await client.get(f"{COINGECKO}/simple/price", params=params)

    print("CoinGecko status:", r.status_code)
    print("CoinGecko response:", r.text)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="CoinGecko error")

    data = r.json()
    cache_set(key, data)
    return data

@app.get("/api/market_chart/{coin_id}")
async def market_chart(coin_id: str, vs_currency: str = "usd", days: int = 7):
    """
    Example: /api/market_chart/bitcoin?vs_currency=usd&days=7
    """
    key = f"chart:{coin_id}:{vs_currency}:{days}"
    cached = cache_get(key)
    if cached:
        return cached

    params = {"vs_currency": vs_currency, "days": days}
    async with httpx.AsyncClient(
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; CryptoTracker/1.0)"}
    ) as client:
        r = await client.get(f"{COINGECKO}/coins/{coin_id}/market_chart", params=params)

    print(f"Market chart {coin_id} status:", r.status_code)
    print("Response:", r.text)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="CoinGecko market chart error")

    data = r.json()
    cache_set(key, data)
    return data

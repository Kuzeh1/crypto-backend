# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

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

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/prices")
async def prices(ids: str = "bitcoin,ethereum", vs_currency: str = "usd", include_24hr_change: bool = True):
    """
    Example: /api/prices?ids=bitcoin,ethereum&vs_currency=usd&include_24hr_change=true
    """
    params = {
        "ids": ids,
        "vs_currencies": vs_currency,
        "include_24hr_change": str(include_24hr_change).lower()
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{COINGECKO}/simple/price", params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="CoinGecko error")
    return r.json()

@app.get("/api/market_chart/{coin_id}")
async def market_chart(coin_id: str, vs_currency: str = "usd", days: int = 7):
    """
    Example: /api/market_chart/bitcoin?vs_currency=usd&days=7
    """
    params = {"vs_currency": vs_currency, "days": days}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{COINGECKO}/coins/{coin_id}/market_chart", params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="CoinGecko market chart error")
    return r.json()

import httpx
import asyncio, time, random
from .. import config

BIRDEYE_API_URL = "https://public-api.birdeye.so"

# Simple in-memory cache: {(address, minute): price}
_PRICE_CACHE: dict[tuple[str, int], float] = {}

_SEM = asyncio.Semaphore(2)  # max 2 concurrent calls to avoid 429

async def get_token_price_at_time(token_address: str, timestamp: int):
    """
    Fetches the historical price of a token from the Birdeye API.
    """
    # Round timestamp to nearest minute to increase cache hits
    price_timestamp = int(timestamp // 60 * 60)

    cache_key = (token_address, price_timestamp)
    cached = _PRICE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    headers = {
        "X-API-KEY": config.BIRDEYE_API_KEY,
        "x-chain": "solana"  # Adding required header
    }
    
    params = {
        "address": token_address,
        "type": "1m", # 1 minute interval
        "time_from": price_timestamp,
        "time_to": price_timestamp + 120 # Check a 2-min window for a match
    }

    print(f"\nFetching price for token {token_address}")
    print(f"Request params: {params}")
    print(f"Using API key: {config.BIRDEYE_API_KEY[:5]}...")

    async with _SEM:  # limit concurrency
        async with httpx.AsyncClient() as client:
            retries = 3
            for attempt in range(1, retries + 1):
                try:
                    response = await client.get(
                        f"{BIRDEYE_API_URL}/defi/history_price", 
                        params=params, 
                        headers=headers,
                        timeout=15.0
                    )
                    if response.status_code == 429:
                        # Rate limited – exponential backoff
                        wait = 0.5 * attempt + random.random() * 0.5
                        print(f"Birdeye 429 rate-limit on attempt {attempt}. Sleeping {wait:.2f}s…")
                        await asyncio.sleep(wait)
                        continue
                    response.raise_for_status()
                    data = response.json()

                    print(f"Response status: {response.status_code}")
                    print(f"Full response: {data}")

                    if data.get("success") and data.get("data", {}).get("items"):
                        price = data["data"]["items"][0].get("value", 0)
                        print(f"Found price: {price}")
                        _PRICE_CACHE[cache_key] = price
                        return price
                    else:
                        print("No historical price data – will try current price endpoint")
                        break
                except httpx.HTTPStatusError as e:
                    print(f"HTTP error ({e.response.status_code}) on attempt {attempt}: {e.response.text}")
                    if e.response.status_code >= 500:
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    break
                except Exception as e:
                    print(f"Unexpected error on attempt {attempt}: {str(e)}")
                    await asyncio.sleep(0.3)

            # Fallback to current price
            try:
                resp = await client.get(
                    f"{BIRDEYE_API_URL}/defi/price", 
                    params={"address": token_address},
                    headers=headers,
                    timeout=10.0
                )
                if resp.status_code == 429:
                    print("429 on fallback current price – giving up.")
                    return 0
                resp.raise_for_status()
                d = resp.json()
                if d.get("success") and d.get("data"):
                    price = d["data"].get("value", 0)
                    print(f"Fallback current price: {price}")
                    _PRICE_CACHE[cache_key] = price
                    return price
            except Exception as e:
                print(f"Fallback current price error: {str(e)}")

    return 0

    # Returning a mock price for now
    mock_prices = {
        "So11111111111111111111111111111111111111112": 140.50,
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyB7uHod": 1.00
    }
    
    return mock_prices.get(token_address, 0) 
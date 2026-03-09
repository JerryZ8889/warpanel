import httpx

GAMMA_API = "https://gamma-api.polymarket.com"

# Known ceasefire market slugs
CEASEFIRE_SLUGS = [
    "us-x-iran-ceasefire-by-march-15",
    "us-x-iran-ceasefire-by-march-31",
    "us-x-iran-ceasefire-by-april-30",
    "us-x-iran-ceasefire-by-may-31",
    "us-x-iran-ceasefire-by-june-30",
]


async def fetch_ceasefire_predictions() -> list[dict]:
    """Fetch ceasefire prediction probabilities from Polymarket."""
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        # Try fetching the parent event first
        try:
            resp = await client.get(
                f"{GAMMA_API}/events",
                params={"slug": "us-x-iran-ceasefire-by", "closed": "false"},
            )
            if resp.status_code == 200:
                events = resp.json()
                if events and len(events) > 0:
                    event = events[0]
                    markets = event.get("markets", [])
                    for market in markets:
                        outcome_prices = market.get("outcomePrices", "[]")
                        if isinstance(outcome_prices, str):
                            import json
                            outcome_prices = json.loads(outcome_prices)
                        yes_price = float(outcome_prices[0]) if outcome_prices else 0

                        results.append({
                            "slug": market.get("slug", ""),
                            "question": market.get("question", ""),
                            "probability": round(yes_price * 100, 1),
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0),
                        })

                    if results:
                        return sorted(results, key=lambda x: x["probability"])
        except Exception:
            pass

        # Fallback: fetch each market individually
        for slug in CEASEFIRE_SLUGS:
            try:
                resp = await client.get(
                    f"{GAMMA_API}/markets",
                    params={"slug": slug},
                )
                if resp.status_code == 200:
                    markets = resp.json()
                    if markets and len(markets) > 0:
                        market = markets[0]
                        outcome_prices = market.get("outcomePrices", "[]")
                        if isinstance(outcome_prices, str):
                            import json
                            outcome_prices = json.loads(outcome_prices)
                        yes_price = float(outcome_prices[0]) if outcome_prices else 0

                        results.append({
                            "slug": slug,
                            "question": market.get("question", slug),
                            "probability": round(yes_price * 100, 1),
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0),
                        })
            except Exception:
                results.append({
                    "slug": slug,
                    "question": slug,
                    "probability": None,
                    "error": "Failed to fetch",
                })

    return sorted(
        [r for r in results if r.get("probability") is not None],
        key=lambda x: x["probability"],
    )

import httpx
import asyncio
from .. import config
from . import transaction_parser

# Updated base URLs – see https://docs.helius.xyz/ for current endpoints
# REST helper (not currently used but kept for completeness)
HELIUS_API_URL = f"https://api.helius.xyz/v0/addresses/{{address}}/transactions/?api-key={config.HELIUS_API_KEY}"

# Universal RPC endpoint for free-tier and pay-as-you-go keys
# If you have a dedicated node, replace with the custom URL shown in the dashboard.
RPC_URL = config.HELIUS_RPC_URL

async def get_parsed_transaction(client: httpx.AsyncClient, signature: str):
    """Fetches a single parsed transaction from Helius. Tries multiple RPC URLs if needed."""
    rpc_candidates = [RPC_URL]
    # Always include the shared endpoint as a fallback – it works for most keys.
    shared = f"https://rpc.helius.xyz/?api-key={config.HELIUS_API_KEY}"
    if shared not in rpc_candidates:
        rpc_candidates.append(shared)

    for rpc in rpc_candidates:
        try:
            response = await client.post(
                rpc,
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "getParsedTransaction",
                    "params": [signature, {"maxSupportedTransactionVersion": 0}],
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("result")
        except httpx.HTTPStatusError as e:
            # 404s or 403s – try next candidate
            if e.response.status_code in {403, 404}:
                print(f"RPC {rpc} returned {e.response.status_code} – trying fallback")
                continue
            else:
                raise
        except Exception as e:
            print(f"Error hitting RPC {rpc}: {str(e)} – trying fallback")
            continue
    return None

async def get_wallet_transactions(wallet_address: str):
    """
    Fetches and parses historical transactions for a given wallet address using the Helius REST API.
    """
    base_url = HELIUS_API_URL.format(address=wallet_address) + "&limit=100"
    async with httpx.AsyncClient() as client:
        tx_overviews = []
        next_before = None
        while True:
            url = base_url + (f"&before={next_before}" if next_before else "")
            resp = await client.get(url, timeout=30.0)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            tx_overviews.extend(batch)
            if len(tx_overviews) >= 500:
                break
            next_before = batch[-1]["signature"]
            if not next_before:
                break

        swaps = []
        for tx in tx_overviews:
            swap = transaction_parser.parse_transaction(tx, wallet_address)
            if swap:
                swaps.append(swap)

        if swaps:
            print(f"Found and parsed {len(swaps)} swaps in enhanced history for {wallet_address}.")
            return swaps

        # Extract signatures (limit to recent 100 to avoid hitting rate limits)
        signatures = [tx.get("signature") for tx in tx_overviews][:100]

        async def fetch_and_parse(sig: str):
            try:
                parsed_tx = await get_parsed_transaction(client, sig)
                if parsed_tx:
                    return transaction_parser.parse_transaction(parsed_tx, wallet_address)
            except Exception as e:
                print(f"Error fetching/parsing tx {sig}: {str(e)}")
            return None

        tasks = [fetch_and_parse(sig) for sig in signatures if sig]
        results = await asyncio.gather(*tasks)

        swaps_rpc = [r for r in results if r]
        print(f"Found and parsed {len(swaps_rpc)} swaps via RPC for {wallet_address}.")
        return swaps_rpc

def get_mock_transactions():
    """Returns mock transactions to ensure frontend has data during development."""
    return [
        {
            "signature": "5h4z...", "timestamp": 1672531200, "type": "SWAP",
            "from_token": "So11111111111111111111111111111111111111112",
            "to_token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyB7uHod",
            "from_amount": 10, "to_amount": 1400
        }
    ] 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from datetime import datetime, timedelta

from .services import helius_service, birdeye_service, transaction_parser
from . import config

app = FastAPI()

# CORS (Cross-Origin Resource Sharing) middleware
# This allows the frontend (running on a different port) to communicate with the backend.
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WalletAnalysisRequest(BaseModel):
    wallet_address: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Wallet Analyzer API"}

async def get_price_for_swap(swap: transaction_parser.Swap):
    """Helper to get prices for both sides of a swap."""
    from_price, to_price = await asyncio.gather(
        birdeye_service.get_token_price_at_time(swap.from_token, swap.timestamp),
        birdeye_service.get_token_price_at_time(swap.to_token, swap.timestamp)
    )
    return from_price, to_price

@app.post("/analyze")
async def analyze_wallet(request: WalletAnalysisRequest):
    swaps = await helius_service.get_wallet_transactions(request.wallet_address)
    
    if not swaps:
        return {"wallet_address": request.wallet_address, "pnl": {}, "chart_data": [], "trade_ledger": []}

    price_tasks = [get_price_for_swap(swap) for swap in swaps]
    prices = await asyncio.gather(*price_tasks)
    
    trade_ledger = []
    for swap, (from_price, to_price) in zip(swaps, prices):
        value_out = swap.from_amount * from_price
        value_in = swap.to_amount * to_price
        pnl = value_in - value_out

        trade_ledger.append({
            "timestamp": swap.timestamp,
            "type": "SWAP",
            "from_token": swap.from_token,
            "to_token": swap.to_token,
            "from_amount": swap.from_amount,
            "to_amount": swap.to_amount,
            "from_price": from_price,
            "to_price": to_price,
            "profit_or_loss": pnl
        })

    # Sort trades by time for accurate windowing
    trade_ledger.sort(key=lambda x: x['timestamp'])

    # Calculate P&L for time windows
    now = datetime.now()
    pnl_7d = sum(t['profit_or_loss'] for t in trade_ledger if datetime.fromtimestamp(t['timestamp']) > now - timedelta(days=7))
    pnl_30d = sum(t['profit_or_loss'] for t in trade_ledger if datetime.fromtimestamp(t['timestamp']) > now - timedelta(days=30))
    pnl_90d = sum(t['profit_or_loss'] for t in trade_ledger if datetime.fromtimestamp(t['timestamp']) > now - timedelta(days=90))
    pnl_all_time = sum(t['profit_or_loss'] for t in trade_ledger)

    # For simplicity, unrealized is 0 as we are only looking at swaps (realized trades)
    pnl_summary = {
        "7d": {"realized": pnl_7d, "unrealized": 0},
        "30d": {"realized": pnl_30d, "unrealized": 0},
        "90d": {"realized": pnl_90d, "unrealized": 0},
        "all_time": {"realized": pnl_all_time, "unrealized": 0},
    }

    # Prepare chart data (cumulative P&L)
    chart_data = []
    cumulative_pnl = 0
    for trade in trade_ledger:
        cumulative_pnl += trade['profit_or_loss']
        chart_data.append({
            "date": datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M'),
            "pnl": cumulative_pnl
        })

    return {
        "wallet_address": request.wallet_address,
        "pnl": pnl_summary,
        "chart_data": chart_data,
        "trade_ledger": trade_ledger,
    } 
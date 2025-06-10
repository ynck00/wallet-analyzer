from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

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
    # Add 60 seconds to simulate copy-trading delay
    delayed_timestamp = swap.timestamp + 60
    from_price, to_price = await asyncio.gather(
        birdeye_service.get_token_price_at_time(swap.from_token, delayed_timestamp),
        birdeye_service.get_token_price_at_time(swap.to_token, delayed_timestamp)
    )
    return from_price, to_price

def validate_timestamp(timestamp):
    """Validate and potentially fix timestamps"""
    if timestamp <= 0:
        return 0
    
    # Check if timestamp is in milliseconds (too large)
    if timestamp > 2000000000:  # Year 2033
        return timestamp // 1000
    
    # Check if timestamp is in the future (more than 1 day)
    now_utc = datetime.utcnow().timestamp()
    if timestamp > now_utc + 86400:  # More than 1 day in future
        print(f"Warning: Future timestamp detected: {timestamp} (current: {now_utc})")
        # Could be milliseconds, try dividing by 1000
        if timestamp // 1000 < now_utc + 86400:
            return timestamp // 1000
    
    return timestamp

async def get_current_price(token_address):
    """Get current price for unrealized P&L calculation"""
    try:
        current_timestamp = int(datetime.utcnow().timestamp())
        return await birdeye_service.get_token_price_at_time(token_address, current_timestamp)
    except:
        # Fallback to mock price if API fails
        mock_prices = {
            "So11111111111111111111111111111111111111112": 140.50,  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyB7uHod": 1.00,  # USDC
        }
        return mock_prices.get(token_address, 0)

@app.post("/analyze")
async def analyze_wallet(request: WalletAnalysisRequest):
    swaps = await helius_service.get_wallet_transactions(request.wallet_address)
    
    if not swaps:
        return {"wallet_address": request.wallet_address, "pnl": {}, "chart_data": [], "trade_ledger": []}

    # Validate and fix timestamps
    for swap in swaps:
        swap.timestamp = validate_timestamp(swap.timestamp)

    price_tasks = [get_price_for_swap(swap) for swap in swaps]
    prices = await asyncio.gather(*price_tasks)
    
    # Track positions for unrealized P&L
    positions = defaultdict(lambda: {"amount": 0.0, "cost_basis": 0.0, "total_cost": 0.0})
    trade_ledger = []
    realized_pnl_by_trade = []
    
    for swap, (from_price, to_price) in zip(swaps, prices):
        # Validate timestamp for display
        display_timestamp = validate_timestamp(swap.timestamp)
        
        value_out = swap.from_amount * from_price
        value_in = swap.to_amount * to_price
        immediate_pnl = value_in - value_out  # This is the immediate arbitrage gain/loss
        
        # Update positions
        # Selling from_token
        if positions[swap.from_token]["amount"] > 0:
            # Calculate realized P&L for the sold portion
            avg_cost_basis = positions[swap.from_token]["cost_basis"]
            realized_pnl = (from_price - avg_cost_basis) * swap.from_amount
            realized_pnl_by_trade.append({
                "timestamp": display_timestamp,
                "realized_pnl": realized_pnl,
                "token": swap.from_token
            })
            
            # Update position
            positions[swap.from_token]["amount"] -= swap.from_amount
            if positions[swap.from_token]["amount"] <= 0:
                positions[swap.from_token] = {"amount": 0.0, "cost_basis": 0.0, "total_cost": 0.0}
        
        # Buying to_token  
        old_amount = positions[swap.to_token]["amount"]
        old_total_cost = positions[swap.to_token]["total_cost"]
        new_amount = old_amount + swap.to_amount
        new_total_cost = old_total_cost + value_in
        
        positions[swap.to_token]["amount"] = new_amount
        positions[swap.to_token]["total_cost"] = new_total_cost
        positions[swap.to_token]["cost_basis"] = new_total_cost / new_amount if new_amount > 0 else 0

        trade_ledger.append({
            "timestamp": display_timestamp,
            "type": "SWAP",
            "from_token": swap.from_token,
            "to_token": swap.to_token,
            "from_amount": swap.from_amount,
            "to_amount": swap.to_amount,
            "from_price": from_price,
            "to_price": to_price,
            "profit_or_loss": immediate_pnl,
            "price_after_60s": to_price  # Add the delayed price for frontend
        })

    # Calculate unrealized P&L for current positions
    unrealized_pnl = 0.0
    current_prices = {}
    
    for token, position in positions.items():
        if position["amount"] > 0:
            current_price = await get_current_price(token)
            current_prices[token] = current_price
            token_unrealized = (current_price - position["cost_basis"]) * position["amount"]
            unrealized_pnl += token_unrealized

    # Sort trades by time for accurate windowing
    trade_ledger.sort(key=lambda x: x['timestamp'])

    # Use UTC for all time calculations and handle edge cases
    now_utc = datetime.utcnow()
    
    def in_time_window(timestamp, days):
        try:
            if timestamp <= 0:
                return False
            trade_time = datetime.utcfromtimestamp(timestamp)
            cutoff_time = now_utc - timedelta(days=days)
            return trade_time >= cutoff_time
        except (ValueError, OSError):
            return False

    # Calculate realized P&L for time windows
    pnl_7d = sum(t['profit_or_loss'] for t in trade_ledger if in_time_window(t['timestamp'], 7))
    pnl_30d = sum(t['profit_or_loss'] for t in trade_ledger if in_time_window(t['timestamp'], 30))
    pnl_90d = sum(t['profit_or_loss'] for t in trade_ledger if in_time_window(t['timestamp'], 90))
    pnl_all_time = sum(t['profit_or_loss'] for t in trade_ledger)

    # For unrealized, we only show current unrealized (not time-windowed, as positions are current)
    pnl_summary = {
        "7d": {"realized": pnl_7d, "unrealized": unrealized_pnl if any(in_time_window(t['timestamp'], 7) for t in trade_ledger) else 0},
        "30d": {"realized": pnl_30d, "unrealized": unrealized_pnl if any(in_time_window(t['timestamp'], 30) for t in trade_ledger) else 0},
        "90d": {"realized": pnl_90d, "unrealized": unrealized_pnl if any(in_time_window(t['timestamp'], 90) for t in trade_ledger) else 0},
        "all_time": {"realized": pnl_all_time, "unrealized": unrealized_pnl},
    }

    # Prepare chart data (cumulative P&L including unrealized)
    chart_data = []
    cumulative_pnl = 0
    for trade in trade_ledger:
        cumulative_pnl += trade['profit_or_loss']
        try:
            trade_time = datetime.utcfromtimestamp(trade['timestamp'])
            formatted_time = trade_time.strftime('%Y-%m-%d %H:%M')
        except (ValueError, OSError):
            formatted_time = "Invalid Date"
            
        chart_data.append({
            "date": formatted_time,
            "pnl": cumulative_pnl + unrealized_pnl  # Include unrealized in chart
        })

    # Add debug info
    debug_info = {
        "total_trades": len(trade_ledger),
        "current_positions": {k: v for k, v in positions.items() if v["amount"] > 0},
        "unrealized_pnl": unrealized_pnl,
        "current_time_utc": now_utc.isoformat(),
    }

    print(f"Debug info: {debug_info}")

    return {
        "wallet_address": request.wallet_address,
        "pnl": pnl_summary,
        "chart_data": chart_data,
        "trade_ledger": trade_ledger,
        "debug": debug_info
    } 
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Helius configuration ---
# Preferred: specify full RPC URL in .env (HELIUS_RPC_URL).
# Fallback: build public shared endpoint from HELIUS_API_KEY.

HELIUS_RPC_URL = os.getenv("HELIUS_RPC_URL")

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")

if not HELIUS_RPC_URL:
    if not HELIUS_API_KEY:
        raise ValueError("Helius API key not found. Please set either HELIUS_RPC_URL or HELIUS_API_KEY in the .env file.")
    # Public shared endpoint (works if RPC access enabled for the key)
    HELIUS_RPC_URL = f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"

if not BIRDEYE_API_KEY:
    raise ValueError("Birdeye API key not found. Please set the BIRDEYE_API_KEY environment variable.") 
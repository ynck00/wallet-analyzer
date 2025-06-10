# Wallet Profitability Analyzer

This project is a web application that analyzes the trading performance of a Solana wallet address to determine how profitable it would have been to copy its trades.

## Overview

The application takes a Solana wallet address as input and performs the following actions:

1.  **Fetches Transaction History**: It uses the Helius API to get all the swaps and token transfers for the wallet.
2.  **Simulates Delayed Trades**: For each transaction, it fetches the token's price 60 seconds *after* the trade occurred using the Birdeye API. This simulates the delay a real copy-trader would face.
3.  **Calculates Profit/Loss**: It calculates both realized and unrealized profit and loss for all positions.
4.  **Displays Results**: The results are displayed in a user-friendly interface, broken down into 7-day, 30-day, 90-day, and all-time windows.
5.  **Visualizes Performance**: A chart shows the wallet's performance over time.
6.  **Provides a Trade Ledger**: A downloadable CSV file of all trades is available.

## Tech Stack

*   **Frontend**: Next.js, React, TypeScript, Tailwind CSS
*   **Backend**: Python, FastAPI
*   **APIs**: Helius (for on-chain data), Birdeye (for price data)

## Getting Started

### Prerequisites

*   Node.js and npm (for the frontend)
*   Python and pip (for the backend)
*   API keys for Helius and Birdeye

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd wallet-profitability-analyzer
    ```

2.  **Backend Setup:**
    ```bash
    cd backend
    pip install -r requirements.txt
    cp .env.example .env 
    # Add your API keys to the .env file
    ```

3.  **Frontend Setup:**
    ```bash
    cd ../frontend
    npm install
    ```

### Running the Application

1.  **Start the backend server:**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    The backend will be running at `http://127.0.0.1:8000`.

2.  **Start the frontend development server:**
    ```bash
    cd ../frontend
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) in your browser.

---

For more details on the project's functionality and architecture, please see the `documents` directory. 
# Wallet Profitability Analyzer

## 1. Core Functionality

The web application allows a user to analyze the historical trading performance of a Solana wallet address. By inputting a wallet address, the user can determine the potential profitability of having copied that wallet's trades.

The application works as follows:

1.  **Input Wallet Address**: The user pastes a valid Solana wallet address into an input field.
2.  **Analysis**: Upon clicking "Analyse", the backend fetches all swap and token transfer transactions for that wallet.
3.  **Delayed Price Simulation**: To simulate a realistic copy-trading scenario, the application fetches the token's price 60 seconds *after* each transaction occurred. This accounts for the delay a human trader would face.
4.  **Comprehensive Position Tracking**: The application tracks the entire lifecycle of a position. It follows tokens even if the original owner moves them to another wallet they control, ensuring that hidden losses are not missed.
5.  **Profit & Loss Calculation**: It calculates both realized (for closed positions) and unrealized (for open positions) profit or loss.
6.  **Time-Windowed Results**: The results are aggregated and displayed for several time windows:
    *   Last 7 Days
    *   Last 30 Days
    *   Last 90 Days
    *   All-Time
7.  **Data Visualization**: The results are presented with a simple chart to visualize performance over time.
8.  **Trade Ledger**: Users can download a detailed trade ledger in CSV format for their own records.

The central question the application answers is: *"If I had followed this wallet, with a one-minute lag, would I be up or down?"*

## 2. External Services

The application relies on two key external services:

*   **Helius**: For fetching on-chain transaction data for the specified wallet.
*   **Birdeye**: For fetching historical token price data (+60 seconds). 
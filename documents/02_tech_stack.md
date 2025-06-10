# Tech Stack

This document outlines the technologies, libraries, and APIs used in the project.

## 1. Frontend

*   **Framework**: Next.js (React)
*   **Styling**: Tailwind CSS
*   **Charting**: Recharts (or a similar library)
*   **Language**: TypeScript

## 2. Backend

*   **Framework**: FastAPI
*   **Language**: Python
*   **Web Server**: Uvicorn
*   **Libraries**:
    *   `httpx` (for making asynchronous API calls to Helius and Birdeye)
    *   `python-dotenv` (for managing environment variables)
    *   `pandas` (for data manipulation and CSV export)

## 3. APIs

*   **Helius API**: Used to fetch historical transaction data for Solana wallets.
    *   **API Documentation**: [https://docs.helius.dev/](https://docs.helius.dev/)
*   **Birdeye API**: Used to fetch historical token price data.
    *   **API Documentation**: [https://docs.birdeye.so/](https://docs.birdeye.so/)

## 4. Development & Deployment

*   **Package Manager (Frontend)**: npm
*   **Package Manager (Backend)**: pip
*   **Version Control**: Git 
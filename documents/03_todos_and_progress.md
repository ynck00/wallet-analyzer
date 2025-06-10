# Todos and Progress

This document tracks the development progress of the application.

## Phase 1: Project Setup & Scaffolding

-   [x] Create project directory structure (`frontend`, `backend`, `documents`)
-   [x] Create `documents/01_functionality.md`
-   [x] Create `documents/02_tech_stack.md`
-   [x] Create `documents/03_todos_and_progress.md`
-   [x] Initialize FastAPI backend
-   [x] Create `backend/requirements.txt`
-   [x] Initialize Next.js frontend
-   [x] Setup Tailwind CSS in the frontend
-   [x] Create `README.md`
-   [x] Create `.gitignore`

## Phase 2: Backend Development

-   [x] Create placeholder `/analyze` endpoint in FastAPI.
-   [x] Set up `.env` for API keys (Helius, Birdeye).
-   [x] Implement Helius service to fetch transactions.
-   [x] Implement Birdeye service to fetch historical prices.
-   [x] Implement core P&L calculation logic.
-   [x] Implement logic for time windows (7d, 30d, 90d, all-time).
-   [x] Implement CSV export functionality.
-   [ ] Implement advanced wallet tracking (Phase 2 enhancement).

## Phase 3: Frontend Development

-   [x] Create UI with wallet address input and "Analyse" button.
-   [x] Connect frontend to backend `/analyze` endpoint.
-   [x] Display results from the backend.
-   [x] Implement chart to visualize P&L.
-   [x] Implement "Download Ledger" button.
-   [x] Style the application using Tailwind CSS.
-   [x] Make the UI responsive.

## Phase 4: Integration & Testing

-   [x] End-to-end testing of the main user flow.
-   [ ] Test with various wallet addresses.
-   [x] Error handling for API failures or invalid wallets.
-   [x] Final review of documentation. 
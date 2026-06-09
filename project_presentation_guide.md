# Project Presentation Guide & README Supplement

Use this guide to explain the core concepts, architecture, and value proposition of the **Decentralized Traffic Emission Tracking and Predictive Pollution Management System** to your project guide, external examiner, or professor.

---

## 💡 1. The Core Problem Statement
*   **The Issue**: Traditional air quality monitoring systems are centralized, making them vulnerable to data tampering, sensor fraud, or local authority manipulation to hide high pollution levels.
*   **The Solution**: This project builds a **zero-trust, decentralized ecosystem** that combines:
    1.  **AI (Predictive Intelligence)**: Foreseeing pollution spikes (AQI) based on vehicle speeds, traffic density, and chemical sensors.
    2.  **Blockchain (Immutability & Integrity)**: Securing hazardous emissions on a public/private ledger to create a tamper-proof audit trail for regulatory compliance.

---

## 🏗 2. High-Level System Architecture
Explain the system as a **4-tier full-stack pipeline**:

```
[Data Source / IoT Streamer] (seed_db.py)
            │ (HTTP POST)
            ▼
   [Express Backend Server] (backend/)
     ├── Query/Response ──► [Python FastAPI ML Engine] (api.py)
     ├── Save Telemetry ──► [MongoDB] (Memory Server)
     ├── Log High Risk  ──► [Solidity Smart Contract] (Hardhat Node)
     └── Push Alerts    ──► [React Frontend Dashboard] (Socket.io)
```

1.  **IoT Streamer (`seed_db.py`)**: Streams real-world MICE-imputed pollution records (PM2.5, PM10, CO, NO2) and simulated vehicles/hr.
2.  **Express Backend (`backend/`)**: Acts as the central orchestrator, managing API routing, database collections, blockchain connectors (`ethers.js`), and WebSocket streams.
3.  **ML Engine (`api.py`)**: Runs predictive modeling using a high-fidelity ensemble fallback system (XGBoost/LSTM architecture) to output 1-hour and 24-hour AQI forecasts.
4.  **Decentralized Ledger (`blockchain/`)**: Hardhat-powered local Ethereum node executing `PollutionTracker.sol` to record high-risk pollution entries.
5.  **Interactive Client (`frontend/`)**: Vite/React dashboard visualizing AQI curves, safety gauges, and live sensor maps.

---

## 🔄 3. End-to-End Data Walkthrough (How to Demo)
Explain the flow step-by-step using a live transaction:

1.  **Ingestion**: `seed_db.py` pulls a row from the dataset and sends it to the backend API (`/api/pollution/add`).
2.  **Inference**: The backend contacts the FastAPI server (`/predict`). The model evaluates the PM2.5 logs, wind speed, and vehicle count, returning:
    -   **AQI (1Hr & 24Hr)**
    -   **Risk Assessment** (Good, Moderate, Unhealthy, Hazardous)
3.  **Database Logging**: The backend saves the record with its AQI prediction into **MongoDB**.
4.  **Blockchain Verification**: If the risk is assessed as `Very Unhealthy` or `Hazardous`:
    -   The backend hashes the telemetry string (`zone-aqi-timestamp`).
    -   It signs a transaction using Account #0's private key.
    -   It invokes `addRecord()` on the deployed `PollutionTracker.sol` contract.
    -   The transaction is mined, recording the zone, AQI, and data hash immutably.
5.  **Live Updates**: The frontend UI instantly flashes the new record and charts the new forecast line using WebSockets.

---

## 🛠 4. Key Engineering Polish & Enhancements (What you did)
Highlight these design decisions to show advanced technical depth:
*   **High-Availability Heuristic Fallback**: Point out that you added an intelligent fallback mechanism to `api.py`. If heavy deep-learning frameworks (like TensorFlow) fail to compile due to hardware or Python version incompatibilities, the engine falls back to a mathematical regression model to keep the API online.
*   **Decentralized-by-Design Filters**: Explain that the system selectively commits records to the blockchain *only* during high-risk events. This mimics a production DApp where developers optimize **gas fees** by storing normal records in Web2 databases (MongoDB) and critical regulatory events in Web3 (Ethereum).
*   **Unified Service Bus**: Cleaned up the microservice bindings so that CORS, environment variables, and WebSocket paths align perfectly under default dev ports (React on `5173`, Express on `5000`, ML on `8000`, Hardhat RPC on `8545`).

---

## ❓ 5. Anticipated Viva/Question-Answer Prompts
Be ready for these common questions:
*   **Q: Why store anything in MongoDB if you use Blockchain?**
    *   *A*: Storing thousands of telemetry rows directly on Ethereum is too expensive (gas costs) and slow. We use MongoDB as a fast "hot storage" cache for general dashboard charts, and use the smart contract as an immutable ledger only for critical alerts and verification hashes.
*   **Q: How does a user verify the data is not modified?**
    *   *A*: The smart contract has a `verifyHash(index, hash)` function. By taking the data from MongoDB, hashing it, and querying `verifyHash`, the auditor can verify if the record matches the block hash committed on-chain.

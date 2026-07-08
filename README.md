# RiskPulse

### AI-Powered MSME Credit Default Prediction & Early Warning System

> **Tagline:** Predict Tomorrow's Risk Today.

RiskPulse is an enterprise-grade AI credit default prediction platform for MSME (Micro, Small, and Medium Enterprises) loans. It evaluates and forecasts credit default risks up to 12 months in advance by fusing structured financial ratios with unstructured qualitative remarks (auditor notes, bank remarks, regulatory filings).

---

## 1. Chosen Vertical & Persona
- **Vertical:** Enterprise Fintech & Commercial Credit Risk Management.
- **Audience/Persona:** Commercial Bank Risk Officers, Credit Analysts, Credit Committees, and Compliance Auditors.
- **Problem Solved:** Traditional credit scoring models (e.g. FICO, CIBIL) are backward-looking and lack the capability to process unstructured remarks or dynamic macro trends. RiskPulse fills this gap by utilizing hyper-tuned ensemble machine learning alongside NLP sentiment scoring.

---

## 2. Approach & Architecture
RiskPulse is designed using a clean, modern **MVC (Model-View-Controller)**, **Repository Pattern**, and **Service Layer** architecture in the backend:

- **API Layer (`FastAPI`)**: High-performance REST endpoints with JWT authorization and Role-Based Access Control (Admin, Risk Analyst).
- **Service Layer**: Tightly encapsulates the business rules (combining financial features, NLP risk weights, model predictions, SHAP explainability, and EWS alert logic).
- **Repository Layer**: Separates raw database access (SQLAlchemy) from business logic, ensuring code is maintainable.
- **Machine Learning Layer**: Trains a competitive ensemble (Random Forest, Logistic Regression, Gradient Boosting, XGBoost, CatBoost, LightGBM) with class balancing (SMOTE / weighted loss) and autotuning.
- **NLP Layer**: Performs sentiment lexicon extraction and keyword risk mapping to index qualitative files (audits, bank logs, remarks) into numeric sentiment risk features.
- **Explainable AI (XAI)**: Generates local feature contributions (waterfall charts) and narrative decision rationales for bankers using SHAP/LIME approximations.

---

## 3. How It Works
1. **Data Ingestion**: A banker uploads borrower financial sheets or logs a new application manually.
2. **Qualitative NLP Parsing**: The user can upload auditor documents or write comments. The NLP parser scans for key distress terms (e.g., "insolvency", "tax penalty", "late payment") to calculate a text sentiment score.
3. **Feature Engineering**: Ratios like Debt-to-Income, Current/Quick ratios, EMI burden, and monthly stability indexes are computed on-the-fly.
4. **Ensemble Classification**: The features are standardized and evaluated against the hyper-tuned ML classifier to generate a 12-month default probability.
5. **Scoring & Alerting**: A standard 0-1000 credit score is computed. Early warning signals (EWS) trigger alerts (e.g., GST filings drop, credit line over-utilization).
6. **XAI Decision Path**: Local contributions are mapped, indicating precisely which factors pushed risk UP (e.g., EMI delays) and which pulled it DOWN (e.g., collateral coverage).

---

## 4. Assumptions Made
1. **Local Sandbox Fallbacks**: Since Windows environments might lack C++ compilers or Docker daemon runtimes, the system supports a **Dual-Mode Setup**:
   - *Local dev*: Uses SQLite, local synchronous background threads (FastAPI `BackgroundTasks`), and a custom Decision Path Explainer if heavy compiled binaries (XGBoost, CatBoost, SHAP) fail to load.
   - *Production*: Uses PostgreSQL, Redis, Celery workers, MLflow, and Docker Compose.
2. **Seeded Data**: Upon first startup, the database is auto-seeded with 4 diverse MSME profiles (from stable low risk to critical distress) to display live data immediately.

---

## 5. Local Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js v18+ & NPM

### Step 1: Start Backend (FastAPI)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   source .venv/bin/activate # On Unix/macOS
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Swagger docs will be live at `http://localhost:8000/docs`.*

### Step 2: Start Frontend (React + Vite)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *The frontend dashboard will be live at `http://localhost:5173`.*

---

## 6. How to Log In (Demo Credentials)
- **Administrator Role** (Allows Retraining ML Models & Uploading Datasets):
  - **Email:** `admin@riskpulse.ai`
  - **Password:** `adminpassword123`
- **Risk Analyst Role** (Allows Inputting Loans & Running Predictions):
  - **Email:** `analyst@riskpulse.ai`
  - **Password:** `analystpassword123`

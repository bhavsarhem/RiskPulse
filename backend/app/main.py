from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.loan import Loan
from backend.app.services.loan_service import loan_service
from backend.app.schemas.loan import LoanCreate
from backend.app.api.v1 import auth, loans, models, dashboard
from backend.app.core.logging import setup_logging, logger

# Initialize Logging
setup_logging()

# Create tables
logger.info("Initializing database tables...")
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="RiskPulse AI MSME Credit Default Prediction & Early Warning System Backend API."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development. In production, specify domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Seed
@app.on_event("startup")
def startup_db_seed():
    db = SessionLocal()
    try:
        # 1. Create Default Admin User
        admin_user = db.query(User).filter(User.email == "admin@riskpulse.ai").first()
        if not admin_user:
            logger.info("Seeding default administrator...")
            db.add(User(
                email="admin@riskpulse.ai",
                hashed_password=get_password_hash("adminpassword123"),
                full_name="RiskPulse Administrator",
                role="admin",
                is_active=True
            ))
            db.commit()

        # 2. Create Default Analyst User
        analyst_user = db.query(User).filter(User.email == "analyst@riskpulse.ai").first()
        if not analyst_user:
            logger.info("Seeding default credit analyst...")
            db.add(User(
                email="analyst@riskpulse.ai",
                hashed_password=get_password_hash("analystpassword123"),
                full_name="Risk Analyst",
                role="analyst",
                is_active=True
            ))
            db.commit()

        # 3. Create Sample MSME Loan Portfolio if empty
        if db.query(Loan).count() == 0:
            logger.info("Seeding sample MSME loans...")
            sample_loans = [
                LoanCreate(
                    borrower_name="Nexus Tech Solutions",
                    industry_sector="Information Technology",
                    loan_amount=150000.0,
                    interest_rate=0.10,
                    term_months=24,
                    monthly_revenue=45000.0,
                    debt=20000.0,
                    current_assets=120000.0,
                    current_liabilities=35000.0,
                    monthly_cash_inflow=48000.0,
                    monthly_cash_outflow=38000.0,
                    gst_growth_pct=0.12,
                    monthly_revenue_growth=0.08,
                    emi_delay_frequency=0,
                    collateral_value=200000.0,
                    credit_utilization=0.35,
                    credit_age_months=48,
                    unstructured_remarks="Stable company. Auditor notes clean audit reporting. Cash reserves are robust. Social signals show steady enterprise traction."
                ),
                LoanCreate(
                    borrower_name="Apex Logistics & Freight",
                    industry_sector="Logistics",
                    loan_amount=250000.0,
                    interest_rate=0.12,
                    term_months=36,
                    monthly_revenue=80000.0,
                    debt=140000.0,
                    current_assets=180000.0,
                    current_liabilities=160000.0,
                    monthly_cash_inflow=85000.0,
                    monthly_cash_outflow=82000.0,
                    gst_growth_pct=-0.08,
                    monthly_revenue_growth=-0.12,
                    emi_delay_frequency=2,
                    collateral_value=150000.0,
                    credit_utilization=0.88,
                    credit_age_months=30,
                    unstructured_remarks="Warning. Cashflow concerns due to high fuel costs and fleet maintenance delays. Bank remarks indicate a bounced EMI last month. Regulatory tax filings are overdue."
                ),
                LoanCreate(
                    borrower_name="Vanguard Organic Foods",
                    industry_sector="Manufacturing",
                    loan_amount=80000.0,
                    interest_rate=0.11,
                    term_months=18,
                    monthly_revenue=28000.0,
                    debt=5000.0,
                    current_assets=45000.0,
                    current_liabilities=48000.0,
                    monthly_cash_inflow=29000.0,
                    monthly_cash_outflow=31000.0,
                    gst_growth_pct=0.02,
                    monthly_revenue_growth=0.01,
                    emi_delay_frequency=0,
                    collateral_value=120000.0,
                    credit_utilization=0.55,
                    credit_age_months=18,
                    unstructured_remarks="Moderate profile. Net profit margins are tight. Increasing competition in raw materials. MCA filings show active disputes resolved."
                ),
                LoanCreate(
                    borrower_name="Starlight Retail Group",
                    industry_sector="Retail Trade",
                    loan_amount=120000.0,
                    interest_rate=0.14,
                    term_months=12,
                    monthly_revenue=65000.0,
                    debt=95000.0,
                    current_assets=70000.0,
                    current_liabilities=90000.0,
                    monthly_cash_inflow=60000.0,
                    monthly_cash_outflow=68000.0,
                    gst_growth_pct=-0.15,
                    monthly_revenue_growth=-0.18,
                    emi_delay_frequency=3,
                    collateral_value=0.0,
                    credit_utilization=0.98,
                    credit_age_months=12,
                    unstructured_remarks="Critical warning. Bankruptcy filing under review or corporate litigation pending. Auditor remarks note a material uncertainty regarding going concern status. Late payments are frequent."
                )
            ]
            for loan in sample_loans:
                loan_service.process_and_create_loan(db, loan)
    finally:
        db.close()

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(loans.router, prefix=f"{settings.API_V1_STR}/loans", tags=["Loans"])
app.include_router(models.router, prefix=f"{settings.API_V1_STR}/models", tags=["Model Administration"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard Analytics"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs": "/docs"
    }

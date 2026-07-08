from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone
from backend.app.core.database import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    borrower_name = Column(String, index=True, nullable=False)
    industry_sector = Column(String, nullable=True)
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0.12)
    term_months = Column(Integer, default=36)
    
    # Financial Statement inputs
    monthly_revenue = Column(Float, nullable=False)
    debt = Column(Float, default=0.0)
    current_assets = Column(Float, default=0.0)
    current_liabilities = Column(Float, default=0.0)
    monthly_cash_inflow = Column(Float, default=0.0)
    monthly_cash_outflow = Column(Float, default=0.0)
    
    # GST / Bureau / EMI signals
    gst_growth_pct = Column(Float, default=0.0)
    monthly_revenue_growth = Column(Float, default=0.0)
    emi_delay_frequency = Column(Integer, default=0)  # number of late payments
    collateral_value = Column(Float, default=0.0)
    credit_utilization = Column(Float, default=0.0)
    credit_age_months = Column(Integer, default=24)
    
    # Unstructured data inputs
    unstructured_remarks = Column(Text, nullable=True)  # Bank remarks, MCA, auditor remarks
    
    # NLP Engine Outputs
    sentiment_risk_score = Column(Float, default=0.0)
    nlp_risk_summary = Column(Text, nullable=True)
    nlp_risk_flags = Column(String, nullable=True)  # JSON encoded list of flags
    
    # Prediction Outputs
    default_probability = Column(Float, default=0.0)
    risk_score = Column(Integer, default=500) # 0 to 1000
    risk_category = Column(String, default="Medium") # Very Low, Low, Medium, High, Critical
    confidence_score = Column(Float, default=1.0)
    recommendation = Column(Text, nullable=True)
    action_priority = Column(String, default="Normal") # Low, Normal, High, Urgent
    early_warning_alerts = Column(Text, nullable=True) # JSON list
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

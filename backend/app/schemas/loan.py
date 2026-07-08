from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class LoanBase(BaseModel):
    borrower_name: str
    industry_sector: Optional[str] = "Other"
    loan_amount: float
    interest_rate: Optional[float] = 0.12
    term_months: Optional[int] = 36
    monthly_revenue: float
    debt: Optional[float] = 0.0
    current_assets: Optional[float] = 0.0
    current_liabilities: Optional[float] = 0.0
    monthly_cash_inflow: Optional[float] = 0.0
    monthly_cash_outflow: Optional[float] = 0.0
    gst_growth_pct: Optional[float] = 0.0
    monthly_revenue_growth: Optional[float] = 0.0
    emi_delay_frequency: Optional[int] = 0
    collateral_value: Optional[float] = 0.0
    credit_utilization: Optional[float] = 0.0
    credit_age_months: Optional[int] = 24
    unstructured_remarks: Optional[str] = None

class LoanCreate(LoanBase):
    pass

class LoanResponse(LoanBase):
    id: int
    sentiment_risk_score: float
    nlp_risk_summary: Optional[str] = None
    nlp_risk_flags: Optional[str] = None
    default_probability: float
    risk_score: int
    risk_category: str
    confidence_score: float
    recommendation: Optional[str] = None
    action_priority: str
    early_warning_alerts: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeatureContribution(BaseModel):
    feature: str
    name: str
    value: str
    impact: float

class LoanExplanationResponse(BaseModel):
    loan_id: int
    borrower_name: str
    default_probability: float
    risk_score: int
    risk_category: str
    risk_factors: List[FeatureContribution]
    mitigating_factors: List[FeatureContribution]
    narrative: str

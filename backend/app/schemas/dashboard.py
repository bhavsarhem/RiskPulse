from typing import Dict, List, Any
from pydantic import BaseModel

class RiskDistributionCard(BaseModel):
    category: str
    count: int
    percentage: float

class AlertItem(BaseModel):
    loan_id: int
    borrower_name: str
    risk_category: str
    alert_type: str  # Critical, Warning, Info
    message: str

class DashboardStats(BaseModel):
    total_active_loans: int
    total_portfolio_value: float
    average_default_probability: float
    risk_distribution: List[RiskDistributionCard]
    alerts: List[AlertItem]
    recent_activity: List[Dict[str, Any]]

import pandas as pd
import numpy as np
from typing import Dict, Any, Union

class FinancialFeatureEngine:
    def __init__(self):
        pass

    @staticmethod
    def calculate_ratios_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates financial ratios for a single borrower data dictionary.
        Safe against division-by-zero.
        """
        feats = {}
        
        # Inputs
        loan_amount = float(data.get("loan_amount", 0.0))
        monthly_revenue = float(data.get("monthly_revenue", 0.0))
        debt = float(data.get("debt", 0.0))
        current_assets = float(data.get("current_assets", 0.0))
        current_liabilities = float(data.get("current_liabilities", 0.0))
        monthly_cash_inflow = float(data.get("monthly_cash_inflow", 0.0))
        monthly_cash_outflow = float(data.get("monthly_cash_outflow", 0.0))
        collateral_value = float(data.get("collateral_value", 0.0))
        credit_utilization = float(data.get("credit_utilization", 0.0))
        interest_rate = float(data.get("interest_rate", 0.12))
        term_months = int(data.get("term_months", 36))
        emi_delay_frequency = int(data.get("emi_delay_frequency", 0))

        # Basic financial ratios
        # 1. Debt to Income (Annualized)
        annual_revenue = monthly_revenue * 12
        feats["debt_to_income"] = debt / annual_revenue if annual_revenue > 0 else (debt / 1.0)
        
        # 2. Current Ratio
        feats["current_ratio"] = current_assets / current_liabilities if current_liabilities > 0 else current_assets
        
        # 3. Quick Ratio (assuming inventory is 30% of current assets)
        quick_assets = current_assets * 0.7
        feats["quick_ratio"] = quick_assets / current_liabilities if current_liabilities > 0 else quick_assets
        
        # 4. Cash Flow Coverage Ratio
        feats["cash_flow_ratio"] = monthly_cash_inflow / monthly_cash_outflow if monthly_cash_outflow > 0 else monthly_cash_inflow
        
        # 5. Loan to Asset ratio (size of loan vs current assets)
        feats["loan_utilization"] = loan_amount / current_assets if current_assets > 0 else 0.0

        # 6. EMI Burden
        # Simple Interest EMI estimation: EMI = (P + P*r*t)/t
        monthly_interest_rate = interest_rate / 12
        total_interest = loan_amount * monthly_interest_rate * term_months
        estimated_monthly_emi = (loan_amount + total_interest) / term_months if term_months > 0 else 0.0
        
        feats["emi_burden"] = estimated_monthly_emi / monthly_revenue if monthly_revenue > 0 else 0.0
        feats["estimated_emi"] = estimated_monthly_emi

        # 7. Collateral Coverage
        feats["collateral_coverage"] = collateral_value / loan_amount if loan_amount > 0 else 1.0

        # Pass-through features
        feats["gst_growth_pct"] = float(data.get("gst_growth_pct", 0.0))
        feats["monthly_revenue_growth"] = float(data.get("monthly_revenue_growth", 0.0))
        feats["emi_delay_frequency"] = emi_delay_frequency
        feats["credit_utilization"] = credit_utilization
        feats["credit_age_months"] = int(data.get("credit_age_months", 24))
        
        # Business stability index (ratios combined with growth)
        # Higher index means safer borrower
        feats["business_stability"] = (
            (feats["current_ratio"] * 0.3) + 
            (feats["cash_flow_ratio"] * 0.3) + 
            (1.0 / (1.0 + emi_delay_frequency)) * 0.4
        )

        return feats

    def create_features_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a pandas dataframe to append financial engineered ratios.
        """
        df_out = df.copy()
        
        # Fill zero for divisions
        epsilon = 1e-5
        
        df_out["debt_to_income"] = df_out["debt"] / (df_out["monthly_revenue"] * 12 + epsilon)
        df_out["current_ratio"] = df_out["current_assets"] / (df_out["current_liabilities"] + epsilon)
        df_out["quick_ratio"] = (df_out["current_assets"] * 0.7) / (df_out["current_liabilities"] + epsilon)
        
        # Cash flows
        inflow = df_out.get("monthly_cash_inflow", df_out["monthly_revenue"])
        outflow = df_out.get("monthly_cash_outflow", df_out["monthly_revenue"] * 0.8)
        df_out["cash_flow_ratio"] = inflow / (outflow + epsilon)
        
        # Loan metrics
        df_out["loan_utilization"] = df_out["loan_amount"] / (df_out["current_assets"] + epsilon)
        
        # EMI
        int_rate = df_out.get("interest_rate", 0.12)
        term = df_out.get("term_months", 36)
        total_interest = df_out["loan_amount"] * (int_rate / 12) * term
        estimated_emi = (df_out["loan_amount"] + total_interest) / term
        df_out["estimated_emi"] = estimated_emi
        df_out["emi_burden"] = estimated_emi / (df_out["monthly_revenue"] + epsilon)
        
        # Collateral and stability
        df_out["collateral_coverage"] = df_out["collateral_value"] / (df_out["loan_amount"] + epsilon)
        
        # Stability index
        delays = df_out.get("emi_delay_frequency", 0)
        df_out["business_stability"] = (
            (df_out["current_ratio"] * 0.3) + 
            (df_out["cash_flow_ratio"] * 0.3) + 
            (1.0 / (1.0 + delays)) * 0.4
        )
        
        # Keep numeric defaults for other features
        df_out["gst_growth_pct"] = df_out.get("gst_growth_pct", 0.0).fillna(0.0)
        df_out["monthly_revenue_growth"] = df_out.get("monthly_revenue_growth", 0.0).fillna(0.0)
        df_out["credit_utilization"] = df_out.get("credit_utilization", 0.0).fillna(0.0)
        df_out["credit_age_months"] = df_out.get("credit_age_months", 24).fillna(24)

        return df_out

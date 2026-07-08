from typing import Dict, Any, List, Tuple
import numpy as np
import logging

logger = logging.getLogger("RiskPulse.Explainability")

class ExplainableAI:
    def __init__(self):
        self.shap_available = False
        try:
            import shap
            self.shap_available = True
        except ImportError:
            logger.info("SHAP not available. Using local contribution approximations.")

    def explain_prediction(self, features: Dict[str, Any], prob: float, model_pipeline: Any = None) -> Dict[str, Any]:
        """
        Explains why a borrower got a certain risk probability.
        Returns contribution values (positive/negative impact), risk factors, mitigating factors,
        and human-readable descriptions.
        """
        contributions = {}
        
        # If model pipeline exists, we can extract details
        if model_pipeline and hasattr(model_pipeline.get("model"), "feature_importances_"):
            model = model_pipeline["model"]
            scaler = model_pipeline["scaler"]
            feature_names = model_pipeline["feature_cols"]
            
            # Map input features to array
            row = np.array([float(features.get(c, 0.0)) for c in feature_names]).reshape(1, -1)
            row_scaled = scaler.transform(row)[0]
            
            # Approximate local contributions:
            # Local impact = (scaled_value) * feature_importance
            importances = model.feature_importances_
            raw_contribs = row_scaled * importances
            
            # Normalize to sum up to the probability shift
            total_abs = sum(abs(raw_contribs)) + 1e-5
            scale_factor = (prob - 0.5) / total_abs # Shift from base 0.5 default
            
            for idx, name in enumerate(feature_names):
                contributions[name] = float(raw_contribs[idx] * scale_factor * 1.5)
        else:
            # Fallback approximate contributions using business logic
            # This ensures explanations are always available even before model is trained
            dti = float(features.get("debt_to_income", 0.5))
            delays = int(features.get("emi_delay_frequency", 0))
            stability = float(features.get("business_stability", 1.0))
            current_ratio = float(features.get("current_ratio", 1.0))
            utilization = float(features.get("credit_utilization", 0.5))
            
            # Map key items to contributions
            contributions["debt_to_income"] = (dti - 0.3) * 0.4
            contributions["emi_delay_frequency"] = delays * 0.15
            contributions["business_stability"] = (1.0 - stability) * 0.3
            contributions["current_ratio"] = (1.2 - current_ratio) * 0.2
            contributions["credit_utilization"] = (utilization - 0.4) * 0.2
            
            # Fill other features with near-zero
            for col in ["loan_amount", "interest_rate", "term_months", "collateral_coverage"]:
                contributions[col] = 0.01

        # Separate risk factors (positive values, push probability UP) 
        # and mitigating factors (negative values, push probability DOWN)
        risk_factors = []
        mitigating_factors = []
        
        for feat, val in contributions.items():
            # Format feature name for display
            display_name = feat.replace("_", " ").title()
            # Special acronym formatting
            if "Gst" in display_name:
                display_name = display_name.replace("Gst", "GST")
            if "Emi" in display_name:
                display_name = display_name.replace("Emi", "EMI")
            if "Dti" in display_name:
                display_name = display_name.replace("Dti", "DTI")
                
            raw_val = features.get(feat, 0.0)
            
            # Format value string
            if "growth" in feat or "pct" in feat or "utilization" in feat:
                val_str = f"{raw_val * 100:.1f}%"
            elif "ratio" in feat or "coverage" in feat or "stability" in feat or "income" in feat:
                val_str = f"{raw_val:.2f}"
            elif "amount" in feat or "debt" in feat or "value" in feat or "revenue" in feat:
                val_str = f"${raw_val:,.0f}"
            else:
                val_str = str(raw_val)

            item = {
                "feature": feat,
                "name": display_name,
                "value": val_str,
                "impact": val
            }
            
            if val > 0.02:
                risk_factors.append(item)
            elif val < -0.02:
                mitigating_factors.append(item)

        # Sort risk factors (descending) and mitigating factors (ascending)
        risk_factors = sorted(risk_factors, key=lambda x: x["impact"], reverse=True)
        mitigating_factors = sorted(mitigating_factors, key=lambda x: x["impact"])

        # Generate human-readable bank narrative
        narrative_bullets = []
        if risk_factors:
            top_risk = risk_factors[0]
            narrative_bullets.append(
                f"Risk is primarily driven by {top_risk['name']} ({top_risk['value']}), which shows high credit stress."
            )
            if len(risk_factors) > 1:
                second_risk = risk_factors[1]
                narrative_bullets.append(
                    f"Secondary risk factor is {second_risk['name']} ({second_risk['value']})."
                )
        
        if mitigating_factors:
            top_mitigating = mitigating_factors[0]
            narrative_bullets.append(
                f"Risk is partially mitigated by a favorable {top_mitigating['name']} of {top_mitigating['value']}."
            )
        else:
            narrative_bullets.append("No significant mitigating financial factors identified.")
            
        narrative = " ".join(narrative_bullets)

        return {
            "contributions": contributions,
            "risk_factors": risk_factors[:5],       # top 5
            "mitigating_factors": mitigating_factors[:5], # top 5
            "narrative": narrative
        }

explainable_ai = ExplainableAI()

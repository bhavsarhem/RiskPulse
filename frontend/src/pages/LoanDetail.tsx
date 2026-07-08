import React, { useState, useEffect } from "react";

import { api } from "../services/api";
import { 
  ArrowLeft, 
  ShieldCheck, 
  ShieldAlert, 
  TrendingUp, 
  Percent, 
  DollarSign, 
  AlertTriangle,
  HelpCircle,
  FileText,
  Activity
} from "lucide-react";

interface LoanDetailData {
  id: number;
  borrower_name: string;
  industry_sector: string;
  loan_amount: number;
  interest_rate: number;
  term_months: number;
  monthly_revenue: number;
  debt: number;
  current_assets: number;
  current_liabilities: number;
  gst_growth_pct: number;
  monthly_revenue_growth: number;
  emi_delay_frequency: number;
  collateral_value: number;
  credit_utilization: number;
  credit_age_months: number;
  unstructured_remarks: string;
  sentiment_risk_score: number;
  nlp_risk_summary: string;
  nlp_risk_flags: string;
  default_probability: number;
  risk_score: number;
  risk_category: string;
  confidence_score: number;
  recommendation: string;
  action_priority: string;
  early_warning_alerts: string;
  created_at: string;
}

interface ExplanationData {
  loan_id: number;
  borrower_name: string;
  default_probability: number;
  risk_score: number;
  risk_category: string;
  risk_factors: Array<{ feature: string; name: string; value: string; impact: number }>;
  mitigating_factors: Array<{ feature: string; name: string; value: string; impact: number }>;
  narrative: string;
}

export const LoanDetail: React.FC<{ loanId: number | null }> = ({ loanId }) => {
  const [loan, setLoan] = useState<LoanDetailData | null>(null);
  const [explanation, setExplanation] = useState<ExplanationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchLoanData = async () => {
    if (!loanId) return;
    try {
      const loanDetails = await api.loans.get(loanId);
      setLoan(loanDetails);
      
      const explainDetails = await api.loans.explain(loanId);
      setExplanation(explainDetails);
    } catch (err: any) {
      setError(err.message || "Failed to load risk profile details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoanData();
  }, [loanId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !loan) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 text-red-700 p-4 rounded-xl max-w-lg mx-auto text-center mt-10">
        <h3 className="font-bold text-lg">Error</h3>
        <p className="mt-2 text-sm">{error || "Could not retrieve risk details."}</p>
        <a href="#loans" className="mt-4 inline-block px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 text-sm font-semibold">
          Back to Portfolio
        </a>
      </div>
    );
  }

  const alerts = loan.early_warning_alerts ? JSON.parse(loan.early_warning_alerts) : [];

  // Ratios Calculations (for local display)
  const annualRev = loan.monthly_revenue * 12;
  const dti = loan.debt / (annualRev || 1);
  const currentRatio = loan.current_assets / (loan.current_liabilities || 1);
  const quickRatio = (loan.current_assets * 0.7) / (loan.current_liabilities || 1);
  const collateralCoverage = loan.collateral_value / (loan.loan_amount || 1);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Back button */}
      <a href="#loans" className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Loan Portfolio
      </a>

      {/* Hero Header Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight">{loan.borrower_name}</h1>
            <span className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-500 font-bold uppercase">
              {loan.industry_sector}
            </span>
          </div>
          <p className="text-slate-500 text-sm">Credit report generated on {new Date(loan.created_at).toLocaleDateString()}</p>
        </div>

        {/* Risk Badges */}
        <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-200 dark:border-slate-800 pt-4 md:pt-0 md:pl-8">
          <div className="text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Risk Score</p>
            <p className="text-3xl font-black text-blue-600 mt-1">{loan.risk_score}</p>
            <span className="text-[10px] text-slate-400">0 - 1000 scale</span>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Default Prob</p>
            <p className="text-3xl font-black text-slate-700 dark:text-slate-350 mt-1">{(loan.default_probability * 100).toFixed(1)}%</p>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-extrabold uppercase mt-1 inline-block ${
              loan.risk_category === "Critical" || loan.risk_category === "High"
                ? "bg-red-500/10 text-red-500"
                : "bg-emerald-500/10 text-emerald-500"
            }`}>
              {loan.risk_category}
            </span>
          </div>
        </div>
      </div>

      {/* Advisory & Recommendation */}
      <div className={`p-6 rounded-2xl border flex gap-4 ${
        loan.risk_category === "Critical" || loan.risk_category === "High"
          ? "bg-red-500/5 border-red-500/15"
          : "bg-emerald-500/5 border-emerald-500/15"
      }`}>
        <div className={`p-3.5 rounded-xl shrink-0 self-start ${
          loan.risk_category === "Critical" || loan.risk_category === "High"
            ? "bg-red-500/10 text-red-500"
            : "bg-emerald-500/10 text-emerald-500"
        }`}>
          {loan.risk_category === "Critical" || loan.risk_category === "High" ? (
            <ShieldAlert className="w-6 h-6" />
          ) : (
            <ShieldCheck className="w-6 h-6" />
          )}
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-lg">AI Credit Committee Recommendation</h3>
            <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
              loan.action_priority === "Urgent" || loan.action_priority === "High"
                ? "bg-red-500/20 text-red-400 animate-pulse"
                : "bg-blue-500/20 text-blue-400"
            }`}>
              {loan.action_priority} Priority
            </span>
          </div>
          <p className="text-sm font-semibold">{loan.recommendation}</p>
        </div>
      </div>

      {/* Financial Indicators & Warnings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Ratios Metrics */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold tracking-tight mb-2">Financial Ratio Analysis</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            
            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Debt to Income</p>
              <p className="text-2xl font-black">{dti.toFixed(2)}</p>
              <p className="text-[10px] text-slate-500">Benchmark: &lt; 0.40</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Current Ratio</p>
              <p className="text-2xl font-black">{currentRatio.toFixed(2)}</p>
              <p className="text-[10px] text-slate-500">Benchmark: &gt; 1.50</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Quick Ratio</p>
              <p className="text-2xl font-black">{quickRatio.toFixed(2)}</p>
              <p className="text-[10px] text-slate-500">Benchmark: &gt; 1.00</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">GST Growth (YOY)</p>
              <p className="text-2xl font-black">{(loan.gst_growth_pct * 100).toFixed(1)}%</p>
              <p className="text-[10px] text-slate-500">Tax compliance growth</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Collateral Coverage</p>
              <p className="text-2xl font-black">{collateralCoverage.toFixed(2)}x</p>
              <p className="text-[10px] text-slate-500">Benchmark: &gt; 1.00x</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">EMI Delays</p>
              <p className="text-2xl font-black text-orange-500">{loan.emi_delay_frequency}</p>
              <p className="text-[10px] text-slate-500">Overdue payments count</p>
            </div>

          </div>
        </div>

        {/* Local Early Warning Radar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col">
          <h2 className="text-xl font-bold tracking-tight mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Borrower Warning Flags
          </h2>
          <div className="space-y-3 flex-1 overflow-y-auto max-h-[300px]">
            {alerts.length === 0 ? (
              <div className="text-slate-400 text-center py-10 text-xs">
                No early warning triggers generated for this profile.
              </div>
            ) : (
              alerts.map((a: any, idx: number) => (
                <div key={idx} className="flex gap-2 p-3 bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 rounded-lg text-xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0 mt-1.5" />
                  <span className="font-semibold text-slate-700 dark:text-slate-300">{a.message}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Explainable AI (SHAP Waterfall local visualization) */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm">
        <h2 className="text-xl font-bold tracking-tight mb-2 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          Explainable AI Decision Path (Local SHAP Contributions)
        </h2>
        <p className="text-slate-500 text-xs mb-6">
          Waterfall mapping showing features that increased prediction risk (positive impact) vs features mitigating risk (negative impact).
        </p>

        {explanation ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* Risk Drivers */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-red-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 pb-1">
                  Top Risk Drivers
                </h3>
                {explanation.risk_factors.length === 0 ? (
                  <p className="text-slate-400 text-xs">No dominant risk drivers detected.</p>
                ) : (
                  explanation.risk_factors.map((f, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-700 dark:text-slate-350">{f.name} ({f.value})</span>
                        <span className="text-red-500 font-bold">+{f.impact.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-850 h-2 rounded-full overflow-hidden">
                        <div className="bg-red-500 h-full rounded-full" style={{ width: `${Math.min(100, f.impact * 150)}%` }} />
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Mitigating Drivers */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-emerald-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 pb-1">
                  Top Mitigating Factors
                </h3>
                {explanation.mitigating_factors.length === 0 ? (
                  <p className="text-slate-400 text-xs">No dominant mitigating factors detected.</p>
                ) : (
                  explanation.mitigating_factors.map((f, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-700 dark:text-slate-350">{f.name} ({f.value})</span>
                        <span className="text-emerald-500 font-bold">{f.impact.toFixed(2)}</span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-850 h-2 rounded-full overflow-hidden">
                        <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${Math.min(100, Math.abs(f.impact) * 150)}%` }} />
                      </div>
                    </div>
                  ))
                )}
              </div>

            </div>

            {/* Narrative explanation */}
            <div className="bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-850 p-4 rounded-xl text-sm leading-relaxed mt-6">
              <span className="font-bold text-slate-800 dark:text-white mr-1">Auditor Narrative:</span>
              <span className="text-slate-600 dark:text-slate-400">{explanation.narrative}</span>
            </div>

          </div>
        ) : (
          <div className="text-center py-10 text-slate-500">
            No explainability data loaded.
          </div>
        )}
      </div>

      {/* Unstructured remarks overview */}
      {loan.unstructured_remarks && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-bold tracking-tight mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-500" />
            Qualitative Audit Log / Remarks NLP Summary
          </h2>
          <div className="bg-slate-50 dark:bg-slate-850 p-4 rounded-xl space-y-3">
            <p className="text-sm whitespace-pre-line text-slate-700 dark:text-slate-300 font-medium">
              {loan.unstructured_remarks}
            </p>
            {loan.nlp_risk_summary && (
              <div className="border-t border-slate-200 dark:border-slate-800 pt-3 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                <span className="font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider block mb-1">
                  NLP Extracted Highlight
                </span>
                {loan.nlp_risk_summary}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Plus, Search, FileText, Upload, AlertCircle, HelpCircle } from "lucide-react";


export const Loans: React.FC = () => {
  const [loans, setLoans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState("");

  // Form states
  const [form, setForm] = useState({
    borrower_name: "",
    industry_sector: "Manufacturing",
    loan_amount: "",
    interest_rate: "0.12",
    term_months: "36",
    monthly_revenue: "",
    debt: "0",
    current_assets: "0",
    current_liabilities: "0",
    monthly_cash_inflow: "0",
    monthly_cash_outflow: "0",
    gst_growth_pct: "0.0",
    monthly_revenue_growth: "0.0",
    emi_delay_frequency: "0",
    collateral_value: "0",
    credit_utilization: "0.0",
    credit_age_months: "24",
    unstructured_remarks: ""
  });

  // NLP extraction states
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [docFeedback, setDocFeedback] = useState("");

  const fetchLoans = async () => {
    try {
      const list = await api.loans.list();
      setLoans(list);
    } catch (err: any) {
      setError("Failed to load loan registry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingDoc(true);
    setDocFeedback("Parsing document via NLP engine...");
    try {
      const result = await api.loans.uploadDocument(file);
      setForm(prev => ({
        ...prev,
        unstructured_remarks: result.summary + "\n\nOriginal Text Snippet:\n" + result.extracted_text_snippet
      }));
      setDocFeedback(`Analyzed successfully. Risk score: ${result.nlp_risk_score.toFixed(1)}, Sentiment: ${result.sentiment_score.toFixed(2)}`);
    } catch (err: any) {
      setDocFeedback(`Error: ${err.message || "Failed to analyze document."}`);
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        ...form,
        loan_amount: parseFloat(form.loan_amount),
        interest_rate: parseFloat(form.interest_rate),
        term_months: parseInt(form.term_months),
        monthly_revenue: parseFloat(form.monthly_revenue),
        debt: parseFloat(form.debt),
        current_assets: parseFloat(form.current_assets),
        current_liabilities: parseFloat(form.current_liabilities),
        monthly_cash_inflow: parseFloat(form.monthly_cash_inflow || form.monthly_revenue),
        monthly_cash_outflow: parseFloat(form.monthly_cash_outflow || "0"),
        gst_growth_pct: parseFloat(form.gst_growth_pct),
        monthly_revenue_growth: parseFloat(form.monthly_revenue_growth),
        emi_delay_frequency: parseInt(form.emi_delay_frequency),
        collateral_value: parseFloat(form.collateral_value),
        credit_utilization: parseFloat(form.credit_utilization),
        credit_age_months: parseInt(form.credit_age_months)
      };

      await api.loans.predict(payload);
      setModalOpen(false);
      // Reset form
      setForm({
        borrower_name: "",
        industry_sector: "Manufacturing",
        loan_amount: "",
        interest_rate: "0.12",
        term_months: "36",
        monthly_revenue: "",
        debt: "0",
        current_assets: "0",
        current_liabilities: "0",
        monthly_cash_inflow: "0",
        monthly_cash_outflow: "0",
        gst_growth_pct: "0.0",
        monthly_revenue_growth: "0.0",
        emi_delay_frequency: "0",
        collateral_value: "0",
        credit_utilization: "0.0",
        credit_age_months: "24",
        unstructured_remarks: ""
      });
      setDocFeedback("");
      fetchLoans();
    } catch (err: any) {
      setError(err.message || "Failed to generate risk prediction.");
    }
  };

  const filteredLoans = loans.filter(l => 
    l.borrower_name.toLowerCase().includes(search.toLowerCase()) ||
    l.industry_sector.toLowerCase().includes(search.toLowerCase()) ||
    l.risk_category.toLowerCase().includes(search.toLowerCase())
  );

  const BADGE_COLORS: Record<string, string> = {
    "Very Low": "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
    "Low": "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
    "Medium": "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
    "High": "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
    "Critical": "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20"
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Loan Portfolio</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Audit registry of MSME loan applications and predictive metrics.</p>
        </div>
        <button 
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition-colors shadow-sm self-start sm:self-center"
        >
          <Plus className="w-5 h-5" />
          Predict Borrower Default
        </button>
      </div>

      {/* Table Filters */}
      <div className="flex items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3.5 py-2 shadow-sm max-w-md">
        <Search className="w-5 h-5 text-slate-400 mr-2" />
        <input 
          type="text" 
          placeholder="Filter by borrower name, sector, or risk..." 
          className="w-full bg-transparent focus:outline-none text-sm"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Main Registry List */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 text-xs font-bold uppercase tracking-wider">
                <th className="px-6 py-4">Borrower Name</th>
                <th className="px-6 py-4">Sector</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Risk Category</th>
                <th className="px-6 py-4">Default Probability</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500">
                    Loading applications...
                  </td>
                </tr>
              ) : filteredLoans.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    No borrower predictions match your filters.
                  </td>
                </tr>
              ) : (
                filteredLoans.map((loan) => (
                  <tr key={loan.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-900 dark:text-white">
                      {loan.borrower_name}
                    </td>
                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{loan.industry_sector}</td>
                    <td className="px-6 py-4 font-semibold">${loan.loan_amount.toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${BADGE_COLORS[loan.risk_category]}`}>
                        {loan.risk_category}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">
                      {(loan.default_probability * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 text-right">
                      <a 
                        href={`#loans/${loan.id}`}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300 px-3 py-1.5 bg-blue-500/5 hover:bg-blue-500/10 rounded-lg transition-all"
                      >
                        Inspect Risk
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Predictor Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto text-white shadow-2xl p-6 md:p-8 space-y-6">
            
            {/* Modal Title */}
            <div className="flex justify-between items-center border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-2xl font-bold">Predict Credit Default Probability</h2>
                <p className="text-slate-400 text-xs mt-1">Run hyper-tuned ensemble prediction on borrower metrics.</p>
              </div>
              <button 
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-3 rounded-lg text-xs flex gap-2">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Document Ingestion OCR Assistant */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                Document Risk Ingestion (Optional)
              </h3>
              <p className="text-xs text-slate-400">
                Upload auditor files, business reports, or remarks. The NLP engine will parse key risks and auto-fill the remarks field.
              </p>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 px-4 py-2 bg-slate-850 hover:bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold cursor-pointer transition-colors">
                  <Upload className="w-4 h-4 text-slate-400" />
                  Select Document
                  <input type="file" className="hidden" accept=".pdf,.txt" onChange={handleFileUpload} />
                </label>
                {uploadingDoc && <span className="text-xs text-blue-400 animate-pulse">Running OCR & Sentiment...</span>}
                {docFeedback && <span className="text-xs text-slate-400 font-semibold">{docFeedback}</span>}
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Section 1: Borrower Profile */}
                <div className="space-y-4 md:col-span-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-1">1. Borrower Profile</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Borrower Name</label>
                      <input required type="text" name="borrower_name" value={form.borrower_name} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" placeholder="e.g. Acme Corp" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Industry Sector</label>
                      <select name="industry_sector" value={form.industry_sector} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm">
                        <option>Manufacturing</option>
                        <option>Information Technology</option>
                        <option>Logistics</option>
                        <option>Retail Trade</option>
                        <option>Construction</option>
                        <option>Healthcare</option>
                        <option>Services</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Collateral Value ($)</label>
                      <input type="number" name="collateral_value" value={form.collateral_value} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                  </div>
                </div>

                {/* Section 2: Loan Parameters */}
                <div className="space-y-4 md:col-span-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-1">2. Loan Parameters</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Loan Request Amount ($)</label>
                      <input required type="number" name="loan_amount" value={form.loan_amount} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Interest Rate (Annual % as decimal)</label>
                      <input type="number" step="0.01" name="interest_rate" value={form.interest_rate} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Term (Months)</label>
                      <input type="number" name="term_months" value={form.term_months} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                  </div>
                </div>

                {/* Section 3: Financial Statements */}
                <div className="space-y-4 md:col-span-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-1">3. Financial Statements</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Monthly Revenue ($)</label>
                      <input required type="number" name="monthly_revenue" value={form.monthly_revenue} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Total Outstanding Debt ($)</label>
                      <input type="number" name="debt" value={form.debt} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Current Assets ($)</label>
                      <input type="number" name="current_assets" value={form.current_assets} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Current Liabilities ($)</label>
                      <input type="number" name="current_liabilities" value={form.current_liabilities} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Monthly Cash Inflow ($)</label>
                      <input type="number" name="monthly_cash_inflow" value={form.monthly_cash_inflow} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Monthly Cash Outflow ($)</label>
                      <input type="number" name="monthly_cash_outflow" value={form.monthly_cash_outflow} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Monthly Revenue Growth (decimal)</label>
                      <input type="number" step="0.01" name="monthly_revenue_growth" value={form.monthly_revenue_growth} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">GST Annual Growth (decimal)</label>
                      <input type="number" step="0.01" name="gst_growth_pct" value={form.gst_growth_pct} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                  </div>
                </div>

                {/* Section 4: Bureau & History */}
                <div className="space-y-4 md:col-span-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-1">4. Credit Bureau & Repayments</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">EMI Delay Counts (Delinquency)</label>
                      <input type="number" name="emi_delay_frequency" value={form.emi_delay_frequency} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Credit Utilization Rate (decimal)</label>
                      <input type="number" step="0.01" name="credit_utilization" value={form.credit_utilization} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">Credit History Age (Months)</label>
                      <input type="number" name="credit_age_months" value={form.credit_age_months} onChange={handleInputChange} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-sm" />
                    </div>
                  </div>
                </div>

                {/* Section 5: Unstructured Audit Remarks */}
                <div className="space-y-4 md:col-span-3">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-1">5. Qualitative / Unstructured Remarks</h4>
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">Internal bank officer remarks, MCA filings overview, or news notes</label>
                    <textarea 
                      name="unstructured_remarks" 
                      rows={3} 
                      value={form.unstructured_remarks} 
                      onChange={handleInputChange} 
                      className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:ring-1 focus:ring-blue-500" 
                      placeholder="Enter qualitative comments or paste extracted document outputs..." 
                    />
                  </div>
                </div>

              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-3 border-t border-slate-800 pt-6">
                <button 
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-slate-700 hover:bg-slate-850 rounded font-semibold text-sm transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded text-sm transition-colors shadow"
                >
                  Trigger Prediction
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
};

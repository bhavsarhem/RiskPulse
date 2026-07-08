import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { 
  TrendingDown, 
  TrendingUp, 
  Activity, 
  DollarSign, 
  AlertTriangle, 
  Percent,
  CheckCircle,
  FileText,
  User
} from "lucide-react";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Legend, 
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from "recharts";

interface DashboardStats {
  total_active_loans: number;
  total_portfolio_value: number;
  average_default_probability: number;
  risk_distribution: Array<{ category: string; count: number; percentage: number }>;
  alerts: Array<{ loan_id: number; borrower_name: string; risk_category: string; alert_type: string; message: string }>;
  recent_activity: Array<{ action: string; details: string; timestamp: string }>;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    try {
      const data = await api.dashboard.getSummary();
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 text-red-700 p-4 rounded-xl max-w-lg mx-auto text-center mt-10">
        <h3 className="font-bold text-lg">Failed to Load Metrics</h3>
        <p className="mt-2 text-sm">{error || "Could not retrieve API statistics."}</p>
        <button 
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // Risk category color mapping
  const COLORS: Record<string, string> = {
    "Very Low": "#10b981", // green
    "Low": "#3b82f6",      // blue
    "Medium": "#f59e0b",   // amber
    "High": "#f97316",     // orange
    "Critical": "#ef4444"  // red
  };

  const chartData = stats.risk_distribution.map(d => ({
    name: d.category,
    value: d.count,
    color: COLORS[d.category] || "#cbd5e1"
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Real-time MSME portfolio risk and warning radar.</p>
        </div>
        <div className="text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 rounded-xl text-slate-500 dark:text-slate-400 flex items-center gap-2 self-start md:self-center shadow-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live Prediction Engine
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Portfolio Size</p>
            <p className="text-3xl font-extrabold">{stats.total_active_loans}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">MSME loan accounts tracked</p>
          </div>
          <div className="p-4 bg-blue-500/10 text-blue-500 rounded-xl">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Portfolio Value</p>
            <p className="text-3xl font-extrabold">${(stats.total_portfolio_value / 1000).toFixed(1)}k</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">Aggregate principal exposure</p>
          </div>
          <div className="p-4 bg-emerald-500/10 text-emerald-500 rounded-xl">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex items-center justify-between col-span-1 sm:col-span-2 lg:col-span-1">
          <div className="space-y-1">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Average Default Risk</p>
            <p className="text-3xl font-extrabold">{(stats.average_default_probability * 100).toFixed(1)}%</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">Weighted default probability</p>
          </div>
          <div className="p-4 bg-amber-500/10 text-amber-500 rounded-xl">
            <Percent className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Charts & Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Risk Distribution Chart */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm lg:col-span-2">
          <h2 className="text-xl font-bold tracking-tight mb-6">Risk Category Distribution</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#cbd5e1" className="dark:hidden" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" className="hidden dark:block" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff'
                  }} 
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Breakdown Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight mb-4">Risk Share</h2>
            <div className="space-y-4">
              {stats.risk_distribution.map((d, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[d.category] }} />
                    <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">{d.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold">{d.count}</span>
                    <span className="text-xs text-slate-400 dark:text-slate-500 ml-2">({d.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="border-t border-slate-200 dark:border-slate-800 pt-4 mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
            Portfolio Health Index: <span className="font-bold text-emerald-500">Strong</span>
          </div>
        </div>
      </div>

      {/* Early Warnings & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Early Warning Radar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Active Early Warnings
            </h2>
            <span className="bg-red-500/10 text-red-500 px-2 py-0.5 rounded text-xs font-bold">
              {stats.alerts.length} Warnings
            </span>
          </div>
          
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {stats.alerts.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                No active early warning alerts in portfolio.
              </div>
            ) : (
              stats.alerts.map((alert, idx) => (
                <div 
                  key={idx} 
                  className={`p-3.5 rounded-xl border flex gap-3 ${
                    alert.alert_type === "Critical" 
                      ? "bg-red-500/5 border-red-500/20 text-red-900 dark:text-red-200" 
                      : "bg-amber-500/5 border-amber-500/20 text-amber-900 dark:text-amber-200"
                  }`}
                >
                  <AlertTriangle className={`w-5 h-5 shrink-0 ${alert.alert_type === "Critical" ? "text-red-500" : "text-amber-500"}`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">{alert.borrower_name}</span>
                      <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                        alert.alert_type === "Critical" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
                      }`}>
                        {alert.alert_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{alert.message}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Audit Timeline */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-bold tracking-tight mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            Audit Action Trail
          </h2>
          <div className="space-y-6 max-h-96 overflow-y-auto pr-2">
            {stats.recent_activity.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                No recent activity logged.
              </div>
            ) : (
              stats.recent_activity.map((act, idx) => (
                <div key={idx} className="flex gap-4 items-start">
                  <div className="relative flex items-center justify-center shrink-0 mt-0.5">
                    <span className="w-3 h-3 rounded-full bg-blue-500" />
                    {idx < stats.recent_activity.length - 1 && (
                      <span className="absolute top-4 bottom-[-24px] left-1.5 w-0.5 bg-slate-200 dark:bg-slate-800" />
                    )}
                  </div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-extrabold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded uppercase tracking-wider">
                        {act.action}
                      </span>
                      <span className="text-[10px] text-slate-400">{act.timestamp}</span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{act.details}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

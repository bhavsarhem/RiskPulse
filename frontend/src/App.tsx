import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Loans } from "./pages/Loans";
import { LoanDetail } from "./pages/LoanDetail";
import { ModelPerformance } from "./pages/ModelPerformance";
import { 
  ShieldAlert, 
  LayoutDashboard, 
  FileText, 
  Settings, 
  LogOut, 
  Menu, 
  X, 
  Sun, 
  Moon,
  User
} from "lucide-react";

const MainAppContent: React.FC = () => {
  const { user, logout } = useAuth();
  
  // Custom hash-based router or simple state router
  const [currentPath, setCurrentPath] = useState<string>("dashboard");
  const [selectedLoanId, setSelectedLoanId] = useState<number | null>(null);
  
  // Responsive mobile sidebar state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Dark mode state
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });

  useEffect(() => {
    // Apply dark class to body
    if (darkMode) {
      document.body.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  // Hook hash-change to support simple router links or custom navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "");
      if (hash.startsWith("loans/")) {
        const parts = hash.split("/");
        const id = parseInt(parts[1]);
        if (!isNaN(id)) {
          setSelectedLoanId(id);
          setCurrentPath("loan-detail");
        }
      } else if (hash) {
        setCurrentPath(hash);
        setSelectedLoanId(null);
      }
    };
    window.addEventListener("hashchange", handleHashChange);
    // Initial check
    handleHashChange();
    return () => {
      window.removeEventListener("hashchange", handleHashChange);
    };
  }, []);

  const navigate = (path: string) => {
    window.location.hash = path;
    setMobileMenuOpen(false);
  };

  if (!user) {
    return <Login />;
  }

  // Render correct page
  const renderPage = () => {
    switch (currentPath) {
      case "dashboard":
        return <Dashboard />;
      case "loans":
        return <Loans />;
      case "loan-detail":
        return <LoanDetail loanId={selectedLoanId} />;
      case "models":
        return <ModelPerformance />;
      default:
        return <Dashboard />;
    }
  };

  const navLinks = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "loans", label: "Loan Portfolio", icon: FileText },
    { id: "models", label: "Model Admin", icon: Settings },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      
      {/* 1. Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-slate-900 text-slate-200 border-r border-slate-800 shrink-0">
        {/* Sidebar Header */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800">
          <ShieldAlert className="w-6 h-6 text-blue-500" />
          <span className="font-extrabold text-lg text-white tracking-wider">RiskPulse</span>
        </div>
        
        {/* Navigation Links */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = currentPath === link.id || (link.id === "loans" && currentPath === "loan-detail");
            return (
              <button
                key={link.id}
                onClick={() => navigate(link.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                  isActive 
                    ? "bg-blue-600 text-white shadow-sm" 
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon className="w-5 h-5" />
                {link.label}
              </button>
            );
          })}
        </nav>
        
        {/* User Profile Footer */}
        <div className="p-4 border-t border-slate-800 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-800 text-slate-400 rounded-lg">
              <User className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{user.role}</p>
              <p className="text-sm font-bold text-white truncate">{user.email}</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-800 hover:bg-red-500/10 hover:border-red-500/20 text-slate-400 hover:text-red-400 rounded-lg text-xs font-bold transition-all"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* 2. Main Page Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        
        {/* Desktop / Mobile Header bar */}
        <header className="h-16 flex items-center justify-between px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-850 shrink-0 shadow-sm relative z-20">
          
          {/* Mobile menu trigger */}
          <button 
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            aria-label="Open navigation menu"
          >
            <Menu className="w-6 h-6" />
          </button>

          {/* Title spacer / Brand for mobile */}
          <div className="md:hidden flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-500" />
            <span className="font-extrabold text-sm text-slate-900 dark:text-white tracking-wider">RiskPulse</span>
          </div>

          <div className="hidden md:block" />

          {/* Settings / Controls */}
          <div className="flex items-center gap-4">
            {/* Dark mode switcher */}
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Toggle theme mode"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </header>

        {/* Dynamic page container */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          {renderPage()}
        </main>
      </div>

      {/* 3. Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 md:hidden flex justify-start">
          <div className="w-64 bg-slate-900 text-slate-200 flex flex-col p-6 animate-slide-in relative border-r border-slate-800">
            {/* Close button */}
            <button 
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
              aria-label="Close navigation menu"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Logo */}
            <div className="flex items-center gap-3 border-b border-slate-850 pb-6 mb-6">
              <ShieldAlert className="w-6 h-6 text-blue-500" />
              <span className="font-extrabold text-lg text-white tracking-wider">RiskPulse</span>
            </div>

            {/* Mobile nav links */}
            <nav className="flex-1 space-y-2">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = currentPath === link.id || (link.id === "loans" && currentPath === "loan-detail");
                return (
                  <button
                    key={link.id}
                    onClick={() => navigate(link.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                      isActive 
                        ? "bg-blue-600 text-white shadow-sm" 
                        : "text-slate-400 hover:bg-slate-800 hover:text-white"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {link.label}
                  </button>
                );
              })}
            </nav>

            {/* User footer */}
            <div className="border-t border-slate-850 pt-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-850 text-slate-400 rounded-lg">
                  <User className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-slate-450 font-bold uppercase tracking-wider">{user.role}</p>
                  <p className="text-sm font-bold text-white truncate">{user.email}</p>
                </div>
              </div>
              <button 
                onClick={logout}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-850 hover:bg-red-500/10 hover:border-red-500/20 text-slate-450 hover:text-red-400 rounded-lg text-xs font-bold transition-all"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainAppContent />
    </AuthProvider>
  );
}

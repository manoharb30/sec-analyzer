'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import SearchBar from '@/components/SearchBar';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleAnalyze = async (ticker: string) => {
    if (!ticker.trim()) return;

    setIsLoading(true);
    try {
      router.push(`/analysis/${ticker.toUpperCase()}`);
    } catch (error) {
      console.error('Navigation error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen">
      <div className="px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative rounded-3xl border border-white/10 overflow-hidden mb-16"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary-700/25 via-primary-500/10 to-transparent" />
          <div className="relative p-8 md:p-12 text-center">
            <div className="flex items-center justify-center gap-2 text-primary-200 text-xs uppercase tracking-widest mb-4">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2H5z" />
              </svg>
              Premium
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight mb-6">
              Turn SEC filings into <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-200 via-sky-200 to-teal-200">investor‑grade insights</span>
            </h1>
            <p className="text-xl text-slate-300/90 mb-8 leading-relaxed max-w-4xl mx-auto">
              Upload a filing or point to EDGAR. Get structured metrics, risk factors with severities, section‑anchored citations, and clean JSON you can ship to your data layer.
            </p>

            {/* Premium pills */}
            <div className="flex flex-wrap justify-center gap-3 mb-8">
              <span className="pill">
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                EDGAR‑only
              </span>
              <span className="pill">
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Item 7 & 8 cites
              </span>
              <span className="pill">
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Numeric strictness
              </span>
            </div>

            {/* Search Section */}
            <div className="search-container max-w-2xl mx-auto">
              <h2 className="text-xl font-semibold text-slate-200 mb-4">
                Start Your Analysis
              </h2>
              <SearchBar
                onAnalyze={handleAnalyze}
                isLoading={isLoading}
                placeholder="Enter ticker symbol (e.g., AAPL, MSFT, TSLA)"
                showSuggestions={true}
              />
            </div>
          </div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="grid md:grid-cols-3 gap-8 lg:gap-12 xl:gap-16"
        >
          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="glass-card p-6"
          >
            <div className="w-12 h-12 bg-primary-500/10 border border-primary-400/20 rounded-xl flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-primary-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-100 mb-3">
              Financial Analysis
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Deep dive into revenue, margins, profitability, and key financial metrics
              with year-over-year comparisons.
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="glass-card p-6"
          >
            <div className="w-12 h-12 bg-success-500/10 border border-success-400/20 rounded-xl flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-success-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-100 mb-3">
              Competitor Intelligence
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Identify direct competitors and get side-by-side financial comparisons
              to understand market positioning.
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="glass-card p-6"
          >
            <div className="w-12 h-12 bg-warning-500/10 border border-warning-400/20 rounded-xl flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-warning-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.99-.833-2.732 0L4.732 18.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-100 mb-3">
              Red Flag Detection
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Advanced algorithms detect accounting anomalies, management issues,
              and early warning signals.
            </p>
          </motion.div>
        </motion.div>

        {/* Popular Tickers */}
        <div className="mt-16 text-center">
          <p className="text-slate-400 mb-6">Popular analyses:</p>
          <div className="flex flex-wrap justify-center gap-3">
            {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA'].map(
              (ticker) => (
                <button
                  key={ticker}
                  onClick={() => handleAnalyze(ticker)}
                  className="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 rounded-lg transition-all duration-200 font-medium backdrop-blur-md"
                  disabled={isLoading}
                >
                  {ticker}
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
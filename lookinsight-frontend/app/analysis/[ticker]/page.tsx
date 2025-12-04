'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import { api, handleApiError } from '@/lib/api';
import { TabType, CompanyMetrics } from '@/types';
import MetricsBar from '@/components/MetricsBar';
import TabNavigation from '@/components/TabNavigation';
import MarkdownDisplay from '@/components/MarkdownDisplay';
import ComparisonTable from '@/components/ComparisonTable';

export default function AnalysisPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [activeTab, setActiveTab] = useState('analysis');
  const [tabs, setTabs] = useState<TabType[]>([
    { id: 'analysis', label: 'Analysis' },
    { id: 'competitors', label: 'Competitors' },
    { id: 'historical', label: 'Historical' },
    { id: 'red-flags', label: 'Red Flags' },
  ]);

  // Fetch main analysis data
  const {
    data: analysisData,
    error: analysisError,
    isLoading: analysisLoading,
  } = useSWR(
    ticker ? `/api/analyze` : null,
    () => api.analyzeCompany(ticker),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5 * 60 * 1000, // 5 minutes
    }
  );

  // Lazy load competitors data
  const {
    data: competitorsData,
    error: competitorsError,
    isLoading: competitorsLoading,
  } = useSWR(
    activeTab === 'competitors' ? `/api/competitors/${ticker}` : null,
    () => api.getCompetitors(ticker),
    {
      revalidateOnFocus: false,
    }
  );

  // Lazy load historical data
  const {
    data: historicalData,
    error: historicalError,
    isLoading: historicalLoading,
  } = useSWR(
    activeTab === 'historical' ? `/api/historical` : null,
    () => api.getHistoricalAnalysis(ticker),
    {
      revalidateOnFocus: false,
    }
  );

  // Update tab states based on loading/error states
  useEffect(() => {
    setTabs((prevTabs) =>
      prevTabs.map((tab) => {
        switch (tab.id) {
          case 'analysis':
            return {
              ...tab,
              isLoading: analysisLoading,
              error: analysisError ? handleApiError(analysisError) : undefined,
              content: analysisData?.content,
            };
          case 'competitors':
            return {
              ...tab,
              isLoading: competitorsLoading,
              error: competitorsError ? handleApiError(competitorsError) : undefined,
              content: competitorsData?.content,
            };
          case 'historical':
            return {
              ...tab,
              isLoading: historicalLoading,
              error: historicalError ? handleApiError(historicalError) : undefined,
              content: historicalData?.content,
            };
          case 'red-flags':
            return {
              ...tab,
              content: historicalData?.content, // Red flags are part of historical analysis
            };
          default:
            return tab;
        }
      })
    );
  }, [
    analysisData,
    analysisError,
    analysisLoading,
    competitorsData,
    competitorsError,
    competitorsLoading,
    historicalData,
    historicalError,
    historicalLoading,
  ]);

  const currentTab = tabs.find((tab) => tab.id === activeTab);
  const companyName = analysisData?.companyName || ticker;

  const renderTabContent = () => {
    if (currentTab?.isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <svg
              className="animate-spin mx-auto h-8 w-8 text-primary-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="mt-2 text-sm text-slate-400">
              {activeTab === 'analysis' && 'Analyzing SEC filings...'}
              {activeTab === 'competitors' && 'Identifying competitors...'}
              {activeTab === 'historical' && 'Processing 5-year trends...'}
              {activeTab === 'red-flags' && 'Detecting warning signals...'}
            </p>
          </motion.div>
        </div>
      );
    }

    if (currentTab?.error) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 border-danger-400/30 bg-danger-500/10"
        >
          <div className="flex items-center">
            <svg
              className="h-5 w-5 text-danger-300 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="text-sm font-medium text-danger-200">
              Error loading {activeTab}
            </h3>
          </div>
          <p className="mt-2 text-sm text-danger-300">{currentTab.error}</p>
        </motion.div>
      );
    }

    switch (activeTab) {
      case 'analysis':
        return (
          <MarkdownDisplay
            content={analysisData?.content || ''}
            showCollapsibleSections={true}
            highlightRisks={false}
          />
        );

      case 'competitors':
        if (competitorsData?.competitors) {
          return (
            <div className="space-y-6">
              <ComparisonTable
                data={competitorsData.competitors}
                isLoading={competitorsLoading}
              />
              {competitorsData.content && (
                <MarkdownDisplay
                  content={competitorsData.content}
                  showCollapsibleSections={false}
                />
              )}
            </div>
          );
        }
        return (
          <MarkdownDisplay
            content={competitorsData?.content || ''}
            showCollapsibleSections={false}
          />
        );

      case 'historical':
        return (
          <MarkdownDisplay
            content={historicalData?.content || ''}
            showCollapsibleSections={true}
            highlightRisks={true}
          />
        );

      case 'red-flags':
        if (historicalData?.redFlags && historicalData.redFlags.length > 0) {
          return (
            <div className="space-y-6">
              {/* Red Flags Summary */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid gap-4 md:grid-cols-3"
              >
                {['high', 'medium', 'low'].map((severity, index) => {
                  const flags = historicalData.redFlags.filter(
                    (flag) => flag.severity === severity
                  );
                  const colorClass =
                    severity === 'high'
                      ? 'danger'
                      : severity === 'medium'
                      ? 'warning'
                      : 'success';

                  return (
                    <motion.div
                      key={severity}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`glass-card p-4 border-${colorClass}-400/30 bg-${colorClass}-500/10`}
                    >
                      <div className="flex items-center">
                        <span
                          className={`text-2xl font-bold text-${colorClass}-200`}
                        >
                          {flags.length}
                        </span>
                        <span
                          className={`ml-2 text-sm font-medium text-${colorClass}-300 capitalize`}
                        >
                          {severity} Risk
                        </span>
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>

              {/* Red Flags Details */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="space-y-4"
              >
                {historicalData.redFlags.map((flag, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className={`glass-card p-4 ${
                      flag.severity === 'high'
                        ? 'border-danger-400/30 bg-danger-500/10'
                        : flag.severity === 'medium'
                        ? 'border-warning-400/30 bg-warning-500/10'
                        : 'border-success-400/30 bg-success-500/10'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4
                          className={`font-semibold ${
                            flag.severity === 'high'
                              ? 'text-danger-200'
                              : flag.severity === 'medium'
                              ? 'text-warning-200'
                              : 'text-success-200'
                          }`}
                        >
                          {flag.description}
                        </h4>
                        <p
                          className={`mt-1 text-sm ${
                            flag.severity === 'high'
                              ? 'text-danger-300'
                              : flag.severity === 'medium'
                              ? 'text-warning-300'
                              : 'text-success-300'
                          }`}
                        >
                          {flag.details}
                        </p>
                      </div>
                      <span
                        className={`px-3 py-1 text-xs font-medium rounded-full ml-4 ${
                          flag.severity === 'high'
                            ? 'bg-danger-500/20 text-danger-200 border border-danger-400/30'
                            : flag.severity === 'medium'
                            ? 'bg-warning-500/20 text-warning-200 border border-warning-400/30'
                            : 'bg-success-500/20 text-success-200 border border-success-400/30'
                        }`}
                      >
                        {flag.category}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          );
        }
        return (
          <MarkdownDisplay
            content={historicalData?.content || ''}
            showCollapsibleSections={true}
            highlightRisks={true}
          />
        );

      default:
        return null;
    }
  };

  if (!ticker) {
    return (
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-2xl font-bold text-slate-100">Invalid Ticker</h1>
          <p className="mt-2 text-slate-400">Please provide a valid ticker symbol.</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Company Header */}
      <div className="border-b border-white/10 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950">
        <div className="px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="md:flex md:items-center md:justify-between"
          >
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-bold text-slate-100">
                {companyName}
              </h1>
              <div className="mt-2 flex items-center text-sm text-slate-400">
                <span className="font-mono text-lg text-primary-300 bg-primary-500/10 px-3 py-1 rounded-lg border border-primary-400/20">
                  {ticker.toUpperCase()}
                </span>
                {analysisData?.analysisDate && (
                  <>
                    <span className="mx-3 text-slate-600">•</span>
                    <span className="text-slate-300">
                      Analyzed {new Date(analysisData.analysisDate).toLocaleDateString()}
                    </span>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Metrics Bar */}
      <MetricsBar
        metrics={analysisData?.metrics}
        isLoading={analysisLoading}
      />

      {/* Tab Navigation */}
      <TabNavigation
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Tab Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {renderTabContent()}
        </motion.div>
      </div>
    </div>
  );
}
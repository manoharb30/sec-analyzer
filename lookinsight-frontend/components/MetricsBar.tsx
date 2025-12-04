'use client';

import { CompanyMetrics } from '@/types';

interface MetricsBarProps {
  metrics?: CompanyMetrics;
  isLoading?: boolean;
}

interface MetricItemProps {
  label: string;
  value: string;
  trend?: 'up' | 'down' | 'flat';
  isLoading?: boolean;
}

function MetricItem({ label, value, trend, isLoading }: MetricItemProps) {
  const getTrendIcon = () => {
    if (!trend) return null;

    switch (trend) {
      case 'up':
        return (
          <svg
            className="w-4 h-4 text-success-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M7 17l9.2-9.2M17 17V7m0 0H7"
            />
          </svg>
        );
      case 'down':
        return (
          <svg
            className="w-4 h-4 text-danger-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 7l-9.2 9.2M7 7v10m0 0h10"
            />
          </svg>
        );
      case 'flat':
        return (
          <svg
            className="w-4 h-4 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 8l4 4-4 4m-12-4h16"
            />
          </svg>
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="metric-card">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-700 rounded mb-2 w-16"></div>
          <div className="h-6 bg-slate-700 rounded w-20"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="metric-card">
      <div className="text-sm text-slate-400 mb-1">{label}</div>
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-slate-100">{value}</span>
        {getTrendIcon()}
      </div>
    </div>
  );
}

export default function MetricsBar({ metrics, isLoading }: MetricsBarProps) {
  const defaultMetrics = [
    { label: 'Revenue', key: 'revenue' },
    { label: 'Operating Margin', key: 'operatingMargin' },
    { label: 'ROE', key: 'roe' },
    { label: 'Debt/Equity', key: 'debtEquity' },
    { label: 'Free Cash Flow', key: 'freeCashFlow' },
  ];

  return (
    <div className="bg-slate-900/50 border-b border-white/10 py-6">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {defaultMetrics.map((metric) => (
            <MetricItem
              key={metric.key}
              label={metric.label}
              value={
                metrics && metric.key in metrics
                  ? (metrics as any)[metric.key]
                  : '--'
              }
              trend={metrics?.trend}
              isLoading={isLoading}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
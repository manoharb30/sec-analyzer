export interface AnalysisData {
  ticker: string;
  companyName: string;
  analysisDate: string;
  content: string;
  metrics?: CompanyMetrics;
}

export interface CompanyMetrics {
  revenue: string;
  revenueGrowth: string;
  grossMargin: string;
  operatingMargin: string;
  netMargin: string;
  roe: string;
  roa: string;
  debtEquity: string;
  currentRatio: string;
  freeCashFlow: string;
  trend?: 'up' | 'down' | 'flat';
}

export interface CompetitorData {
  ticker: string;
  companyName: string;
  businessOverlap: string;
  competitiveStrength: 'high' | 'medium' | 'low';
  rank: number;
}

export interface ComparisonData {
  targetCompany: CompetitorData;
  competitors: CompetitorData[];
  content: string;
}

export interface HistoricalData {
  ticker: string;
  companyName: string;
  analysisDate: string;
  analysisPeriod: string;
  content: string;
  redFlags: RedFlag[];
}

export interface RedFlag {
  category: 'accounting' | 'executive' | 'operational' | 'cashflow' | 'business';
  severity: 'high' | 'medium' | 'low';
  description: string;
  details: string;
}

export interface TabType {
  id: string;
  label: string;
  content?: string;
  isLoading?: boolean;
  error?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
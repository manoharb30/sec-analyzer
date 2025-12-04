import { AnalysisData, ComparisonData, HistoricalData, ApiResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchWithError<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new ApiError(
      `API Error: ${response.status} ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export const api = {
  // Analyze single company
  async analyzeCompany(ticker: string, year?: string): Promise<AnalysisData> {
    return fetchWithError<AnalysisData>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ ticker, year: year || '2024' }),
    });
  },

  // Get competitors for a company
  async getCompetitors(ticker: string): Promise<ComparisonData> {
    return fetchWithError<ComparisonData>(`/api/competitors/${ticker}`);
  },

  // Compare companies
  async compareCompanies(
    ticker: string,
    competitors: string[]
  ): Promise<ComparisonData> {
    return fetchWithError<ComparisonData>('/api/compare', {
      method: 'POST',
      body: JSON.stringify({ ticker, competitors }),
    });
  },

  // Get historical analysis
  async getHistoricalAnalysis(
    ticker: string,
    years?: number
  ): Promise<HistoricalData> {
    return fetchWithError<HistoricalData>('/api/historical', {
      method: 'POST',
      body: JSON.stringify({ ticker, years: years || 5 }),
    });
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return fetchWithError<{ status: string }>(`${API_BASE_URL}/health`);
  },
};

// SWR fetcher function
export const fetcher = (url: string) => fetch(url).then((res) => res.json());

// Error handler for SWR
export const handleApiError = (error: any): string => {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};
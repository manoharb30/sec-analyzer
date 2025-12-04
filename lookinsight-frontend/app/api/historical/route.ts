import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const ticker = searchParams.get('ticker');

    if (!ticker) {
      return NextResponse.json(
        { error: 'Ticker symbol is required' },
        { status: 400 }
      );
    }

    // Call Python backend API for historical analysis
    const response = await fetch(`${PYTHON_API_URL}/historical/${ticker.toUpperCase()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Python API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Transform the response to match our frontend types
    const transformedData = {
      ticker: ticker.toUpperCase(),
      companyName: data.company_name || data.companyName || ticker,
      analysisDate: new Date().toISOString(),
      content: data.analysis || data.content || '',
      redFlags: data.red_flags?.map((flag: any) => ({
        category: flag.category || 'Other',
        severity: flag.severity || 'medium',
        description: flag.description || flag.title || '',
        details: flag.details || flag.explanation || '',
        year: flag.year || new Date().getFullYear(),
      })) || [],
      trends: data.trends ? {
        revenue: data.trends.revenue || '--',
        profitability: data.trends.profitability || '--',
        efficiency: data.trends.efficiency || '--',
        leverage: data.trends.leverage || '--',
        liquidity: data.trends.liquidity || '--',
      } : undefined,
      keyInsights: data.key_insights || data.insights || [],
    };

    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Historical API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch historical analysis',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
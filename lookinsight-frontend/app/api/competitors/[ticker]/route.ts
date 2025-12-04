import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { ticker: string } }
) {
  try {
    const { ticker } = params;

    if (!ticker) {
      return NextResponse.json(
        { error: 'Ticker symbol is required' },
        { status: 400 }
      );
    }

    // Call Python backend API for competitor analysis
    const response = await fetch(`${PYTHON_API_URL}/competitors/${ticker.toUpperCase()}`, {
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
      targetCompany: {
        ticker: ticker.toUpperCase(),
        companyName: data.target_company?.name || data.target_company?.company_name || ticker,
        businessOverlap: '',
        competitiveStrength: 'high' as const,
        rank: 0,
      },
      competitors: data.competitors?.map((competitor: any, index: number) => ({
        ticker: competitor.ticker || '',
        companyName: competitor.company_name || competitor.name || '',
        businessOverlap: competitor.business_overlap || competitor.overlap || '',
        competitiveStrength: competitor.competitive_strength || competitor.threat_level || 'medium',
        rank: competitor.rank || index + 1,
      })) || [],
      content: data.analysis || data.content || '',
    };

    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Competitors API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch competitors',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
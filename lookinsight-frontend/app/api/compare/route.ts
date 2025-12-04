import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ticker, competitors } = body;

    if (!ticker) {
      return NextResponse.json(
        { error: 'Ticker symbol is required' },
        { status: 400 }
      );
    }

    if (!competitors || !Array.isArray(competitors) || competitors.length === 0) {
      return NextResponse.json(
        { error: 'At least one competitor is required' },
        { status: 400 }
      );
    }

    // Call Python backend API for financial comparison
    const response = await fetch(`${PYTHON_API_URL}/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker: ticker.toUpperCase(),
        competitors: competitors.map((c: string) => c.toUpperCase()),
      }),
    });

    if (!response.ok) {
      throw new Error(`Python API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Transform the response to match our frontend types
    const transformedData = {
      targetCompany: {
        ticker: ticker.toUpperCase(),
        companyName: data.target_company?.name || ticker,
        businessOverlap: '',
        competitiveStrength: 'high' as const,
        rank: 0,
      },
      competitors: data.competitors?.map((competitor: any, index: number) => ({
        ticker: competitor.ticker || '',
        companyName: competitor.company_name || competitor.name || '',
        businessOverlap: competitor.business_overlap || '',
        competitiveStrength: competitor.competitive_strength || 'medium',
        rank: index + 1,
      })) || [],
      content: data.analysis || data.content || data.comparison_results || '',
    };

    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Compare API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to compare companies',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Force Next.js recompilation

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  console.log(`🌐 [FRONTEND API] POST /api/analyze - Request started at ${new Date().toISOString()}`);

  try {
    const body = await request.json();
    const { ticker, year = '2024' } = body;
    console.log(`🌐 [FRONTEND API] Request body:`, { ticker, year });

    if (!ticker) {
      console.log(`🌐 [FRONTEND API] ERROR: No ticker provided`);
      return NextResponse.json(
        { error: 'Ticker symbol is required' },
        { status: 400 }
      );
    }

    console.log(`🌐 [FRONTEND API] Calling Python backend: ${PYTHON_API_URL}/analyze`);
    console.log(`🌐 [FRONTEND API] Payload:`, { ticker: ticker.toUpperCase(), year });

    // Call Python backend API
    const response = await fetch(`${PYTHON_API_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ticker: ticker.toUpperCase(), year }),
    });

    console.log(`🌐 [FRONTEND API] Python backend response status: ${response.status} ${response.statusText}`);
    console.log(`🌐 [FRONTEND API] Response headers:`, Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      throw new Error(`Python API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`🌐 [FRONTEND API] Python backend response data preview:`, {
      ticker: data.ticker,
      companyName: data.companyName,
      contentLength: data.content?.length || 0,
      hasMetrics: !!data.metrics
    });

    // DETAILED CONSOLE LOGGING - Show full backend response
    console.log(`🔍 [FRONTEND API] COMPLETE BACKEND RESPONSE:`, data);
    console.log(`📄 [FRONTEND API] CONTENT SAMPLE:`, data.content?.substring(0, 200) + '...');
    console.log(`💰 [FRONTEND API] METRICS RECEIVED:`, data.metrics);

    // Transform the response to match our frontend types
    const transformedData = {
      ticker: ticker.toUpperCase(),
      companyName: data.companyName || data.company_name || ticker,
      analysisDate: new Date().toISOString(),
      content: data.analysis || data.content || '',
      metrics: data.metrics ? {
        revenue: data.metrics.revenue || '--',
        revenueGrowth: data.metrics.revenue_growth || '--',
        grossMargin: data.metrics.gross_margin || '--',
        operatingMargin: data.metrics.operating_margin || '--',
        netMargin: data.metrics.net_margin || '--',
        roe: data.metrics.roe || '--',
        roa: data.metrics.roa || '--',
        debtEquity: data.metrics.debt_equity || '--',
        currentRatio: data.metrics.current_ratio || '--',
        freeCashFlow: data.metrics.free_cash_flow || '--',
      } : undefined,
    };

    const duration = Date.now() - startTime;
    console.log(`🌐 [FRONTEND API] SUCCESS - Request completed in ${duration}ms`);
    console.log(`🌐 [FRONTEND API] Transformed data preview:`, {
      ticker: transformedData.ticker,
      companyName: transformedData.companyName,
      contentLength: transformedData.content?.length || 0,
      hasMetrics: !!transformedData.metrics
    });

    // DETAILED CONSOLE LOGGING - Show final transformed data
    console.log(`🎯 [FRONTEND API] FINAL TRANSFORMED DATA:`, transformedData);
    console.log(`📝 [FRONTEND API] FINAL CONTENT SAMPLE:`, transformedData.content?.substring(0, 200) + '...');
    console.log(`📊 [FRONTEND API] FINAL METRICS:`, transformedData.metrics);

    return NextResponse.json(transformedData);
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`🌐 [FRONTEND API] ERROR after ${duration}ms:`, error);
    console.error(`🌐 [FRONTEND API] Error details:`, {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : 'Unknown error',
      cause: error instanceof Error ? error.cause : undefined
    });

    return NextResponse.json(
      {
        error: 'Failed to analyze company',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
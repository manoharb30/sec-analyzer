import { NextRequest } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const ticker = searchParams.get('ticker');
  const filingType = searchParams.get('filing_type') || '10-K';

  if (!ticker) {
    return new Response(
      `data: ${JSON.stringify({ step: 'error', progress: 100, error: 'Ticker is required' })}\n\n`,
      {
        status: 400,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      }
    );
  }

  try {
    // Proxy SSE request to Python backend
    const response = await fetch(
      `${PYTHON_API_URL}/analyze/stream?ticker=${encodeURIComponent(ticker)}&filing_type=${encodeURIComponent(filingType)}`,
      {
        headers: {
          'Accept': 'text/event-stream',
        },
      }
    );

    if (!response.ok) {
      return new Response(
        `data: ${JSON.stringify({ step: 'error', progress: 100, error: `Backend error: ${response.status}` })}\n\n`,
        {
          status: response.status,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          },
        }
      );
    }

    // Stream the response directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error) {
    console.error('SSE proxy error:', error);
    return new Response(
      `data: ${JSON.stringify({ step: 'error', progress: 100, error: 'Failed to connect to backend' })}\n\n`,
      {
        status: 500,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      }
    );
  }
}

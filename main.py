"""
SEC Analyzer CLI
Command-line interface for financial analysis of SEC filings.

Usage:
    python main.py AAPL                    # Analyze Apple's 10-K
    python main.py MSFT --filing 10-Q      # Analyze Microsoft's 10-Q
    python main.py NVDA --save             # Save results to JSON
"""

import asyncio
import argparse
import json
from typing import Dict, Any, Optional
from agents.financial_analyst import FinancialAnalystAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyze_ticker(
    ticker: str,
    filing_type: str = "10-K",
    confidence_threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Run financial analysis for a ticker using the new RAG-based pipeline.

    Flow:
    1. Download SEC filing from EDGAR
    2. Index in Pinecone with smart chunking
    3. Extract metrics via RAG + LLM
    4. Generate analysis and recommendation
    """
    print(f"\n{'='*60}")
    print(f"SEC Financial Analyzer")
    print(f"{'='*60}")
    print(f"Ticker: {ticker}")
    print(f"Filing Type: {filing_type}")
    print(f"Confidence Threshold: {confidence_threshold:.0%}")
    print(f"{'='*60}\n")

    # Create and run the agent
    agent = FinancialAnalystAgent(
        ticker=ticker,
        filing_type=filing_type,
        confidence_threshold=confidence_threshold
    )

    try:
        analysis = await agent.run()
    except Exception as e:
        logger.error(f"Analysis failed with exception: {e}")
        return {
            'ticker': ticker,
            'status': 'failed',
            'error': str(e),
            'recommendation': 'UNABLE TO ANALYZE',
            'confidence': 0.0
        }

    # Handle failed analysis
    if analysis.get('status') == 'failed':
        print(f"\n[FAILED] Analysis Failed for {ticker}")
        print(f"Reason: {analysis.get('error', 'Unknown error')}")

        if analysis.get('suggestions'):
            print("\nSuggestions:")
            for suggestion in analysis['suggestions']:
                print(f"  - {suggestion}")

        return analysis

    return analysis


def print_analysis(analysis: Dict[str, Any]):
    """Pretty print the analysis results."""
    if not analysis or analysis.get('status') == 'failed':
        return

    print("\n" + "="*60)
    print(f"ANALYSIS RESULTS: {analysis['ticker']}")
    print("="*60)

    # Company info
    if analysis.get('company_name'):
        print(f"\nCompany: {analysis['company_name']}")
    if analysis.get('filing_date'):
        print(f"Filing Date: {analysis['filing_date']}")
    if analysis.get('filing_type'):
        print(f"Filing Type: {analysis['filing_type']}")

    # Metrics
    print("\n" + "-"*40)
    print("FINANCIAL METRICS")
    print("-"*40)
    metrics = analysis.get('metrics', {})
    if metrics:
        for key, data in metrics.items():
            display_value = data.get('display', data.get('value', 'N/A'))
            confidence = data.get('confidence', 0)
            section = data.get('section', '')
            confidence_indicator = "[HIGH]" if confidence > 0.7 else "[MED]" if confidence > 0.4 else "[LOW]"
            print(f"  {key.replace('_', ' ').title()}: {display_value} {confidence_indicator}")
    else:
        print("  No metrics extracted")

    # Insights
    print("\n" + "-"*40)
    print("KEY INSIGHTS")
    print("-"*40)
    insights = analysis.get('insights', [])
    if insights:
        for i, insight in enumerate(insights, 1):
            # Truncate long insights
            if len(insight) > 200:
                insight = insight[:200] + "..."
            print(f"  {i}. {insight}")
    else:
        print("  No insights generated")

    # Risks
    print("\n" + "-"*40)
    print("RISK FACTORS")
    print("-"*40)
    risks = analysis.get('risks', [])
    if risks:
        for risk in risks:
            print(f"  [!] {risk}")
    else:
        print("  No significant risks identified")

    # Opportunities
    print("\n" + "-"*40)
    print("OPPORTUNITIES")
    print("-"*40)
    opportunities = analysis.get('opportunities', [])
    if opportunities:
        for opp in opportunities:
            print(f"  [+] {opp}")
    else:
        print("  No specific opportunities identified")

    # Recommendation
    print("\n" + "="*60)
    recommendation = analysis.get('recommendation', 'N/A')
    confidence = analysis.get('confidence', 0)

    # Color-code recommendation (using text markers since terminal might not support colors)
    if 'BUY' in recommendation:
        rec_marker = "[BUY]"
    elif 'SELL' in recommendation:
        rec_marker = "[SELL]"
    else:
        rec_marker = "[HOLD]"

    print(f"RECOMMENDATION: {rec_marker} {recommendation}")
    print(f"CONFIDENCE: {confidence:.1%}")
    print("="*60)


def save_analysis(analysis: Dict[str, Any], filename: str = None):
    """Save analysis to JSON file."""
    if not analysis:
        print("No analysis to save")
        return

    if not filename:
        ticker = analysis.get('ticker', 'unknown')
        filing_type = analysis.get('filing_type', '10-K')
        filename = f"{ticker}_{filing_type}_analysis.json"

    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\nAnalysis saved to: {filename}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='SEC Filing Financial Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py AAPL                    # Analyze Apple's 10-K
    python main.py MSFT --filing 10-Q      # Analyze Microsoft's 10-Q
    python main.py NVDA --confidence 0.8   # Higher confidence threshold
    python main.py GOOGL --save            # Save results to JSON

Data Flow:
    1. Download SEC filing from EDGAR
    2. Index in Pinecone with smart chunking (preserves tables)
    3. Extract metrics via RAG + LLM
    4. Generate analysis and recommendation
        """
    )

    parser.add_argument(
        'ticker',
        help='Stock ticker symbol (e.g., AAPL, MSFT, NVDA)'
    )
    parser.add_argument(
        '--filing', '-f',
        default='10-K',
        choices=['10-K', '10-Q'],
        help='Filing type: 10-K (annual) or 10-Q (quarterly). Default: 10-K'
    )
    parser.add_argument(
        '--confidence', '-c',
        type=float,
        default=0.7,
        help='Confidence threshold (0.0-1.0). Default: 0.7'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Save analysis results to JSON file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output filename for JSON (only used with --save)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress detailed logging output'
    )

    args = parser.parse_args()

    # Adjust logging level if quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Validate confidence threshold
    if not 0.0 <= args.confidence <= 1.0:
        print("Error: Confidence threshold must be between 0.0 and 1.0")
        return

    # Run the analysis
    analysis = asyncio.run(
        analyze_ticker(
            ticker=args.ticker.upper(),
            filing_type=args.filing,
            confidence_threshold=args.confidence
        )
    )

    # Print results
    if analysis:
        print_analysis(analysis)

        # Save if requested
        if args.save:
            save_analysis(analysis, args.output)


if __name__ == "__main__":
    main()

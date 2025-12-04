import asyncio
import argparse
import json
from typing import Dict, Any
from agents.financial_analyst import FinancialAnalystAgent
from services.fallback_service import FallbackDataService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def analyze_ticker(ticker: str, confidence_threshold: float = 0.7):
    """Run financial analysis for a ticker"""
    print(f"\n{'='*60}")
    print(f"Starting Financial Analysis for {ticker}")
    print(f"{'='*60}\n")
    
    agent = FinancialAnalystAgent(
        ticker=ticker,
        confidence_threshold=confidence_threshold
    )
    
    analysis = await agent.run()
    
    if analysis.get('status') == 'failed':
        print(f"\n❌ Analysis Failed for {ticker}")
        print(f"Reason: {analysis['error']}")
        print("\n💡 Suggestions:")
        for suggestion in analysis.get('suggestions', []):
            print(f"  • {suggestion}")
        
        # Try fallback
        print("\n🔄 Attempting fallback analysis...")
        fallback = FallbackDataService()
        alternatives = await fallback.try_alternative_sources(ticker)
        
        if alternatives.get('status') == 'not_found':
            print(f"❌ {alternatives['message']}")
            return None
        else:
            print("📊 Limited data available:")
            for key, value in alternatives.items():
                print(f"  • {key}: {value}")
    
    return analysis

def print_analysis(analysis: Dict[str, Any]):
    """Pretty print the analysis results"""
    print("\n" + "="*60)
    print(f"Analysis Results for {analysis['ticker']}")
    print("="*60)
    
    print("\n📊 Key Metrics:")
    for key, data in analysis['metrics'].items():
        print(f"  {key}: {data['display']}")
    
    print("\n💡 Key Insights:")
    for insight in analysis['insights']:
        print(f"  • {insight}")
    
    print("\n⚠️ Risks:")
    for risk in analysis['risks']:
        print(f"  • {risk}")
    
    print("\n🎯 Opportunities:")
    for opp in analysis['opportunities']:
        print(f"  • {opp}")
    
    print(f"\n📈 Recommendation: {analysis['recommendation']}")
    print(f"Confidence: {analysis['confidence']:.1%}")
    print("="*60)

def save_analysis(analysis: Dict[str, Any], filename: str = None):
    """Save analysis to JSON file"""
    if not filename:
        filename = f"{analysis['ticker']}_analysis.json"
    
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Analysis saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Financial Analysis Agent')
    parser.add_argument('ticker', help='Stock ticker symbol (e.g., HYLN)')
    parser.add_argument('--confidence', type=float, default=0.7,
                      help='Confidence threshold (0-1)')
    parser.add_argument('--save', action='store_true',
                      help='Save analysis to JSON file')
    
    args = parser.parse_args()
    
    # Run the analysis
    analysis = asyncio.run(analyze_ticker(args.ticker, args.confidence))
    
    # Print results
    print_analysis(analysis)
    
    # Save if requested
    if args.save:
        save_analysis(analysis)
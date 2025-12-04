import asyncio
import sys
from datetime import datetime
from agents.financial_analyst import FinancialAnalystAgent

class TeeOutput:
    """Capture output to both console and file"""
    def __init__(self, file_handle):
        self.file = file_handle
        self.stdout = sys.stdout

    def write(self, text):
        self.stdout.write(text)  # Print to console
        self.file.write(text)    # Write to file

    def flush(self):
        self.stdout.flush()
        self.file.flush()

async def test_hyln():
    """Test the agent with HYLN ticker"""

    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agent_test_output_{timestamp}.txt"

    with open(filename, 'w') as f:
        # Write header to file
        f.write(f"Financial Analyst Agent Test Output\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"=" * 60 + "\n\n")

        # Redirect stdout to both console and file
        original_stdout = sys.stdout
        sys.stdout = TeeOutput(f)

        try:
            print("Testing Financial Analyst Agent with GOEV (Canoo)...")

            agent = FinancialAnalystAgent("GOEV (Canoo)")
            analysis = await agent.run()

            print(f"\nAnalysis complete!")
            print(f"Ticker: {analysis['ticker']}")
            print(f"Confidence: {analysis['confidence']:.1%}")
            print(f"Recommendation: {analysis['recommendation']}")

            # Show detailed results
            print(f"\n=== DETAILED ANALYSIS ===")
            print(f"Metrics found: {list(analysis.get('metrics', {}).keys())}")
            print(f"Insights: {len(analysis.get('insights', []))}")
            print(f"Risks: {len(analysis.get('risks', []))}")
            print(f"Opportunities: {len(analysis.get('opportunities', []))}")

            # Show actual metric values
            print(f"\n=== METRIC VALUES ===")
            metrics = analysis.get('metrics', {})
            for key, value in metrics.items():
                print(f"{key}: {value}")

            # Show insights and opportunities
            print(f"\n=== INSIGHTS ===")
            for insight in analysis.get('insights', []):
                print(f"• {insight}")

            print(f"\n=== OPPORTUNITIES ===")
            for opp in analysis.get('opportunities', []):
                print(f"• {opp}")

            return analysis

        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return None

        finally:
            # Restore stdout
            sys.stdout = original_stdout
            print(f"\n✅ Test output also saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(test_hyln())
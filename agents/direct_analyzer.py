"""
Direct SEC Filing Analyzer
Simple RAG-based analysis without CrewAI complexity
Supports streaming progress updates via generator
"""

import os
import sys
from typing import Dict, Any, Generator, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.pinecone_rag import SECFilingRAG


class DirectSECAnalyzer:
    """Direct RAG-based SEC filing analyzer - fast and reliable"""

    def __init__(self):
        self.rag = SECFilingRAG()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def analyze_with_progress(self, filing_text: str, ticker: str, filing_type: str = "10-K") -> Generator[Dict[str, Any], None, None]:
        """
        Analyze with streaming progress updates.
        Yields progress events, final event contains full result.
        """
        try:
            # Step 1: Index the filing
            yield {"step": "indexing", "progress": 10, "message": f"Indexing {ticker} filing..."}

            index_result = self.rag.index_filing(
                filing_text=filing_text,
                ticker=ticker,
                filing_type=filing_type,
                filing_date="latest"
            )

            if not index_result.get("success"):
                yield {
                    "step": "error",
                    "progress": 100,
                    "error": f"Failed to index filing: {index_result.get('error')}"
                }
                return

            chunks_indexed = index_result.get('chunks_indexed', 0)
            yield {"step": "indexed", "progress": 25, "message": f"Indexed {chunks_indexed} chunks"}

            # Step 2: Extract financial metrics
            yield {"step": "financials", "progress": 35, "message": "Extracting financial metrics..."}
            financials = self._extract_financials(ticker)
            yield {"step": "financials_done", "progress": 50, "message": "Financial metrics extracted"}

            # Step 3: Extract risks
            yield {"step": "risks", "progress": 55, "message": "Analyzing risk factors..."}
            risks = self._extract_risks(ticker)
            yield {"step": "risks_done", "progress": 70, "message": "Risk analysis complete"}

            # Step 4: Extract business info
            yield {"step": "business", "progress": 75, "message": "Analyzing business model..."}
            business = self._extract_business(ticker)
            yield {"step": "business_done", "progress": 85, "message": "Business analysis complete"}

            # Step 5: Generate report
            yield {"step": "report", "progress": 90, "message": "Generating comprehensive report..."}
            report = self._generate_report(ticker, financials, risks, business)

            # Final result
            yield {
                "step": "complete",
                "progress": 100,
                "message": "Analysis complete",
                "result": {
                    "success": True,
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "analysis": report,
                    "metrics": financials.get("metrics", {}),
                    "sections": {
                        "financials": financials,
                        "risks": risks,
                        "business": business
                    }
                }
            }

        except Exception as e:
            yield {
                "step": "error",
                "progress": 100,
                "error": str(e)
            }

    def analyze(self, filing_text: str, ticker: str, filing_type: str = "10-K") -> Dict[str, Any]:
        """
        Analyze an SEC filing using direct RAG queries

        Args:
            filing_text: The full text of the SEC filing
            ticker: Stock ticker symbol
            filing_type: Type of filing (10-K or 10-Q)

        Returns:
            Dictionary with analysis results
        """
        print(f"Indexing {ticker} filing...")

        # Step 1: Index the filing
        index_result = self.rag.index_filing(
            filing_text=filing_text,
            ticker=ticker,
            filing_type=filing_type,
            filing_date="latest"
        )

        if not index_result.get("success"):
            return {
                "success": False,
                "ticker": ticker,
                "error": f"Failed to index filing: {index_result.get('error')}"
            }

        print(f"Indexed {index_result.get('chunks_indexed', 0)} chunks")

        # Step 2: Query for each analysis section
        print("Extracting financial metrics...")
        financials = self._extract_financials(ticker)

        print("Analyzing risks...")
        risks = self._extract_risks(ticker)

        print("Analyzing business...")
        business = self._extract_business(ticker)

        # Step 3: Generate comprehensive report
        print("Generating report...")
        report = self._generate_report(ticker, financials, risks, business)

        return {
            "success": True,
            "ticker": ticker,
            "filing_type": filing_type,
            "analysis": report,
            "metrics": financials.get("metrics", {}),
            "sections": {
                "financials": financials,
                "risks": risks,
                "business": business
            }
        }

    def _extract_financials(self, ticker: str) -> Dict[str, Any]:
        """Extract key financial metrics"""
        queries = [
            ("revenue", "What is the total revenue or net sales?"),
            ("net_income", "What is the net income?"),
            ("gross_margin", "What is the gross profit and gross margin percentage?"),
            ("operating_income", "What is the operating income?"),
            ("cash", "What is the total cash and cash equivalents?"),
            ("debt", "What is the total debt?"),
            ("eps", "What is the earnings per share (EPS)?"),
        ]

        metrics = {}
        details = []

        for metric_name, query in queries:
            result = self.rag.query(query, ticker, top_k=5)
            if result.get("success"):
                answer = result.get("answer", "")
                metrics[metric_name] = answer
                details.append(f"**{metric_name.replace('_', ' ').title()}**: {answer}")

        return {
            "metrics": metrics,
            "summary": "\n".join(details)
        }

    def _extract_risks(self, ticker: str) -> Dict[str, Any]:
        """Extract key risk factors"""
        result = self.rag.query(
            "What are the top 5 most important risk factors?",
            ticker,
            top_k=8
        )

        return {
            "summary": result.get("answer", "Risk information not available"),
            "sections": result.get("sections_searched", [])
        }

    def _extract_business(self, ticker: str) -> Dict[str, Any]:
        """Extract business description and strategy"""
        queries = [
            ("description", "What is the company's business description?"),
            ("products", "What are the main products and services?"),
            ("competition", "Who are the main competitors?"),
        ]

        details = {}
        for key, query in queries:
            result = self.rag.query(query, ticker, top_k=5)
            if result.get("success"):
                details[key] = result.get("answer", "")

        return details

    def _generate_report(self, ticker: str, financials: Dict, risks: Dict, business: Dict) -> str:
        """Generate a comprehensive analysis report"""
        prompt = f"""You are an expert financial analyst. Create a comprehensive investment report for {ticker} based on the following extracted information from their SEC filing.

## Financial Metrics
{financials.get('summary', 'No financial data available')}

## Risk Factors
{risks.get('summary', 'No risk data available')}

## Business Description
{business.get('description', 'No description available')}

## Products and Services
{business.get('products', 'No product information available')}

## Competition
{business.get('competition', 'No competition information available')}

---

Create a well-structured investment report with these sections:

1. **Executive Summary** (2-3 paragraphs summarizing the company and key metrics)

2. **Financial Highlights**
   - Present the key financial metrics in a clear format
   - Include specific numbers from the data above

3. **Business Overview**
   - Describe the business model
   - List key products/services
   - Note competitive position

4. **Risk Assessment**
   - Summarize the top risks
   - Rate each as High/Medium/Low impact

5. **Key Takeaways**
   - 5-7 bullet points for investors

Use the ACTUAL NUMBERS from the financial metrics. Be specific and cite the data provided."""

        response = self.llm.invoke(prompt)
        return response.content


# For backward compatibility with the API
class SECAnalysisCrew:
    """Wrapper to maintain API compatibility"""

    def __init__(self):
        self.analyzer = DirectSECAnalyzer()

    def analyze(self, filing_text: str, ticker: str, filing_type: str = "10-K") -> Dict[str, Any]:
        return self.analyzer.analyze(filing_text, ticker, filing_type)

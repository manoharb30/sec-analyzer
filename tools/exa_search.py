"""
Exa Search Tool for finding SEC filing URLs
Uses Exa AI to search for the latest 10-K/10-Q filings on SEC EDGAR
"""

import os
from typing import Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()


class SECFilingSearchInput(BaseModel):
    """Input schema for SEC Filing Search"""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, MSFT)")
    filing_type: str = Field(default="10-K", description="Filing type: 10-K (annual) or 10-Q (quarterly)")


class SECFilingSearchTool(BaseTool):
    """Tool to search for SEC filing URLs using Exa AI"""

    name: str = "SEC Filing Search"
    description: str = (
        "Search for the latest SEC 10-K or 10-Q filing URL for a given stock ticker. "
        "Returns the SEC EDGAR URL where the filing can be downloaded."
    )
    args_schema: Type[BaseModel] = SECFilingSearchInput

    def __init__(self):
        super().__init__()
        self._exa = Exa(api_key=os.getenv("EXA_API_KEY"))

    def _run(self, ticker: str, filing_type: str = "10-K") -> dict:
        """
        Search for SEC filing URL using Exa AI

        Args:
            ticker: Stock ticker symbol
            filing_type: 10-K (annual) or 10-Q (quarterly)

        Returns:
            dict with filing URL, company name, and filing info
        """
        # Build search query for SEC EDGAR
        query = f"site:sec.gov {ticker} {filing_type} 2024 filing htm"

        try:
            # Search using Exa
            results = self._exa.search(
                query=query,
                num_results=5,
                use_autoprompt=True
            )

            # Filter for SEC EDGAR URLs
            sec_urls = []
            for result in results.results:
                url = result.url
                if "sec.gov" in url and "/Archives/edgar/" in url:
                    # Prefer .htm files (the actual filing)
                    if url.endswith(".htm") or url.endswith(".html"):
                        sec_urls.append({
                            "url": url,
                            "title": result.title,
                            "published_date": getattr(result, "published_date", None)
                        })

            if not sec_urls:
                # Try alternate search
                return self._fallback_search(ticker, filing_type)

            # Return the best match
            best_match = sec_urls[0]

            return {
                "success": True,
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "filing_url": best_match["url"],
                "title": best_match["title"],
                "published_date": best_match["published_date"],
                "all_results": sec_urls[:3]  # Top 3 for reference
            }

        except Exception as e:
            return {
                "success": False,
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "error": str(e),
                "filing_url": None
            }

    def _fallback_search(self, ticker: str, filing_type: str) -> dict:
        """Fallback search with different query"""
        try:
            # More specific query
            query = f"SEC EDGAR {ticker} {filing_type} annual report 2024"

            results = self._exa.search(
                query=query,
                num_results=10,
                use_autoprompt=True
            )

            for result in results.results:
                url = result.url
                if "sec.gov" in url:
                    return {
                        "success": True,
                        "ticker": ticker.upper(),
                        "filing_type": filing_type,
                        "filing_url": url,
                        "title": result.title,
                        "published_date": getattr(result, "published_date", None),
                        "note": "Found via fallback search"
                    }

            return {
                "success": False,
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "error": "No SEC filing found",
                "filing_url": None
            }

        except Exception as e:
            return {
                "success": False,
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "error": f"Fallback search failed: {str(e)}",
                "filing_url": None
            }


# Test function
if __name__ == "__main__":
    tool = SECFilingSearchTool()
    result = tool._run("AAPL", "10-K")
    print(f"Result: {result}")

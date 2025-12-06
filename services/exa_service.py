"""
Exa Service - DEPRECATED

This service previously used Exa Answer API for metric extraction.
That approach has been replaced by the MetricExtractor service which uses:
1. Pinecone RAG to retrieve relevant document chunks
2. LLM to extract specific metrics from context

For metric extraction, use:
    from services.metric_extractor import MetricExtractor
    extractor = MetricExtractor()
    result = extractor.extract_metric("revenue", "AAPL")

For SEC filing URL search, use:
    from tools.exa_search import SECFilingSearchTool
    search = SECFilingSearchTool()
    result = search._run("AAPL", "10-K")
"""

import os
import warnings
from typing import Dict, Any, Optional
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()


class ExaService:
    """
    DEPRECATED: Use MetricExtractor for financial metric extraction.

    This class is kept for backward compatibility but will be removed in future versions.
    It now wraps MetricExtractor for metric-related queries.
    """

    def __init__(self):
        self.client = Exa(api_key=os.getenv('EXA_API_KEY'))
        self._metric_extractor = None
        warnings.warn(
            "ExaService is deprecated. Use MetricExtractor for metric extraction "
            "or SECFilingSearchTool for URL discovery.",
            DeprecationWarning,
            stacklevel=2
        )

    @property
    def metric_extractor(self):
        """Lazy initialization of MetricExtractor."""
        if self._metric_extractor is None:
            from services.metric_extractor import MetricExtractor
            self._metric_extractor = MetricExtractor()
        return self._metric_extractor

    async def get_metric(self, question: str, ticker: str = None) -> Dict[str, Any]:
        """
        DEPRECATED: Get a specific metric.

        This method now redirects to MetricExtractor for RAG-based extraction.
        The ticker must be provided and the filing must be indexed in Pinecone first.
        """
        warnings.warn(
            "ExaService.get_metric() is deprecated. Use MetricExtractor.extract_metric() instead.",
            DeprecationWarning,
            stacklevel=2
        )

        if not ticker:
            # Try to extract ticker from question
            import re
            ticker_match = re.search(r'\b([A-Z]{1,5})\b', question)
            if ticker_match:
                ticker = ticker_match.group(1)
            else:
                return {'answer': None, 'citations': [], 'error': 'Ticker not provided'}

        # Extract metric name from question
        metric_name = self._extract_metric_name(question)

        # Use MetricExtractor
        result = self.metric_extractor.extract_metric(metric_name, ticker)

        # Convert to old format for backward compatibility
        if result.get('success'):
            return {
                'answer': f"{result.get('raw_value', result.get('value'))}",
                'citations': [result.get('source_section', 'SEC Filing')],
                'value': result.get('value'),
                'confidence': result.get('confidence', 0.0)
            }
        else:
            return {
                'answer': None,
                'citations': [],
                'error': result.get('error', 'Extraction failed')
            }

    def _extract_metric_name(self, question: str) -> str:
        """Extract metric name from a question string."""
        question_lower = question.lower()

        metric_keywords = {
            'revenue': ['revenue', 'sales', 'net sales'],
            'net_income': ['net income', 'profit', 'earnings'],
            'roe': ['return on equity', 'roe'],
            'debt_to_equity': ['debt-to-equity', 'debt to equity', 'd/e'],
            'operating_margin': ['operating margin'],
            'gross_margin': ['gross margin'],
            'revenue_growth': ['growth rate', 'revenue growth', 'yoy'],
            'eps': ['earnings per share', 'eps'],
            'total_debt': ['total debt', 'debt'],
            'cash': ['cash', 'cash equivalents'],
        }

        for metric, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return metric

        return 'revenue'  # Default

    def parse_numeric_value(self, text: str) -> Optional[float]:
        """
        DEPRECATED: Parse numeric value from text.

        This functionality is now handled internally by MetricExtractor.
        Kept for backward compatibility.
        """
        warnings.warn(
            "ExaService.parse_numeric_value() is deprecated. "
            "MetricExtractor handles value parsing internally.",
            DeprecationWarning,
            stacklevel=2
        )

        if not text:
            return None

        import re

        # Check for failure indicators
        failure_indicators = [
            "cannot provide",
            "do not contain",
            "not available",
            "unable to",
            "sorry",
            "no specific"
        ]
        if any(indicator in text.lower() for indicator in failure_indicators):
            return None

        # Look for patterns
        patterns = [
            (r'\$\s*([\d,]+(?:\.\d+)?)\s*(billion|B)', 1e9),
            (r'\$\s*([\d,]+(?:\.\d+)?)\s*(million|M)', 1e6),
            (r'\$\s*([\d,]+(?:\.\d+)?)\s*(thousand|K)', 1e3),
            (r'\$\s*([\d,]+(?:\.\d+)?)', 1),
            (r'([-]?[\d.]+)\s*%', 1),  # Percentage
            (r'([-]?[\d.]+)\s*x', 1),  # Ratio
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    return value * multiplier
                except ValueError:
                    continue

        return None


def search_sec_filing(ticker: str, filing_type: str = "10-K") -> Dict[str, Any]:
    """
    Search for SEC filing URL using Exa.

    This is the recommended way to use Exa in this architecture -
    for URL discovery only, not for content extraction.

    Args:
        ticker: Stock ticker symbol
        filing_type: Filing type (10-K or 10-Q)

    Returns:
        Dict with filing URL and metadata
    """
    from tools.exa_search import SECFilingSearchTool

    search_tool = SECFilingSearchTool()
    return search_tool._run(ticker, filing_type)

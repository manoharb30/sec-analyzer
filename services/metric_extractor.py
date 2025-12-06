"""
Metric Extractor Service
Extracts specific financial metrics from SEC filings using RAG + LLM.

This replaces the Exa Answer API approach with a more reliable
document-grounded extraction method.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class MetricExtractor:
    """
    Extracts financial metrics from indexed SEC filings using RAG.

    Flow:
    1. Query Pinecone RAG for relevant chunks
    2. Use LLM to extract specific numeric value from context
    3. Parse and validate the extracted value
    4. Return structured metric result
    """

    # Standard financial metrics with extraction patterns
    METRIC_DEFINITIONS = {
        'revenue': {
            'aliases': ['total revenue', 'net sales', 'total net sales', 'net revenue'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s total revenue or net sales for the most recent fiscal year? Provide the exact dollar amount."
        },
        'net_income': {
            'aliases': ['net income', 'net earnings', 'profit'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s net income for the most recent fiscal year? Provide the exact dollar amount."
        },
        'gross_profit': {
            'aliases': ['gross profit', 'gross margin'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s gross profit for the most recent fiscal year? Provide the exact dollar amount."
        },
        'operating_income': {
            'aliases': ['operating income', 'operating profit', 'income from operations'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s operating income for the most recent fiscal year? Provide the exact dollar amount."
        },
        'total_assets': {
            'aliases': ['total assets'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What are {ticker}'s total assets? Provide the exact dollar amount."
        },
        'total_debt': {
            'aliases': ['total debt', 'long-term debt', 'total liabilities'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s total debt (including long-term and short-term)? Provide the exact dollar amount."
        },
        'cash': {
            'aliases': ['cash', 'cash and cash equivalents', 'cash equivalents'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s cash and cash equivalents? Provide the exact dollar amount."
        },
        'operating_margin': {
            'aliases': ['operating margin'],
            'unit': 'percentage',
            'typical_section': 'md_and_a',
            'question_template': "What is {ticker}'s operating margin percentage?"
        },
        'gross_margin': {
            'aliases': ['gross margin'],
            'unit': 'percentage',
            'typical_section': 'md_and_a',
            'question_template': "What is {ticker}'s gross margin percentage?"
        },
        'revenue_growth': {
            'aliases': ['revenue growth', 'sales growth', 'yoy growth'],
            'unit': 'percentage',
            'typical_section': 'md_and_a',
            'question_template': "What is {ticker}'s year-over-year revenue growth rate? Provide the percentage."
        },
        'eps': {
            'aliases': ['earnings per share', 'eps', 'diluted eps'],
            'unit': 'dollars_per_share',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s earnings per share (EPS)? Provide both basic and diluted if available."
        },
        'debt_to_equity': {
            'aliases': ['debt to equity', 'debt-to-equity ratio', 'd/e ratio'],
            'unit': 'ratio',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s debt-to-equity ratio?"
        },
        'roe': {
            'aliases': ['return on equity', 'roe'],
            'unit': 'percentage',
            'typical_section': 'md_and_a',
            'question_template': "What is {ticker}'s return on equity (ROE)? Provide the percentage."
        },
        'free_cash_flow': {
            'aliases': ['free cash flow', 'fcf'],
            'unit': 'dollars',
            'typical_section': 'financial_statements',
            'question_template': "What is {ticker}'s free cash flow? Provide the exact dollar amount."
        },
    }

    def __init__(self, rag_instance=None):
        """
        Initialize MetricExtractor.

        Args:
            rag_instance: Optional SECFilingRAG instance. If not provided, one will be created.
        """
        self.rag = rag_instance
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,  # Zero temperature for precise extraction
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def _get_rag(self):
        """Lazy initialization of RAG instance."""
        if self.rag is None:
            from rag.pinecone_rag import SECFilingRAG
            self.rag = SECFilingRAG()
        return self.rag

    def extract_metric(self, metric_name: str, ticker: str) -> Dict[str, Any]:
        """
        Extract a specific financial metric from the indexed filing.

        Args:
            metric_name: Name of the metric (e.g., 'revenue', 'net_income', 'operating_margin')
            ticker: Stock ticker

        Returns:
            Dict with:
                - success: bool
                - metric_name: str
                - value: float or None
                - raw_value: str (original text)
                - unit: str (dollars, percentage, ratio)
                - source_section: str
                - confidence: float (0-1)
                - context: str (relevant text snippet)
        """
        metric_key = metric_name.lower().replace(' ', '_').replace('-', '_')

        # Get metric definition
        metric_def = self.METRIC_DEFINITIONS.get(metric_key)
        if not metric_def:
            # Try to find by alias
            for key, definition in self.METRIC_DEFINITIONS.items():
                if metric_name.lower() in [a.lower() for a in definition['aliases']]:
                    metric_def = definition
                    metric_key = key
                    break

        if not metric_def:
            # Use generic extraction
            metric_def = {
                'aliases': [metric_name],
                'unit': 'unknown',
                'typical_section': None,
                'question_template': f"What is {{ticker}}'s {metric_name}? Provide the exact value."
            }

        # Build the question
        question = metric_def['question_template'].format(ticker=ticker)

        # Query RAG
        rag = self._get_rag()

        # First try with section filter if we know the typical section
        rag_result = None
        if metric_def.get('typical_section'):
            rag_result = rag.query(
                question=question,
                ticker=ticker,
                top_k=5,
                section_filter=metric_def['typical_section']
            )

        # If no results or low confidence, try without filter
        if not rag_result or not rag_result.get('success'):
            rag_result = rag.query(
                question=question,
                ticker=ticker,
                top_k=8
            )

        if not rag_result.get('success'):
            return {
                'success': False,
                'metric_name': metric_key,
                'value': None,
                'error': rag_result.get('error', 'Failed to query RAG'),
                'ticker': ticker
            }

        # Extract structured value using LLM
        extraction_result = self._extract_value_from_answer(
            answer=rag_result['answer'],
            metric_name=metric_key,
            unit=metric_def['unit'],
            ticker=ticker
        )

        # Build result
        source_sections = rag_result.get('sections_searched', [])

        return {
            'success': extraction_result['success'],
            'metric_name': metric_key,
            'value': extraction_result.get('value'),
            'raw_value': extraction_result.get('raw_value'),
            'unit': metric_def['unit'],
            'source_section': source_sections[0] if source_sections else 'unknown',
            'confidence': extraction_result.get('confidence', 0.0),
            'context': rag_result['answer'][:500],  # Truncated context
            'ticker': ticker
        }

    def _extract_value_from_answer(self, answer: str, metric_name: str,
                                    unit: str, ticker: str) -> Dict[str, Any]:
        """
        Use LLM to extract a structured numeric value from the RAG answer.
        """
        extraction_prompt = f"""Extract the specific numeric value for "{metric_name}" from the following text.

TEXT:
{answer}

INSTRUCTIONS:
1. Find the most recent/relevant value for {metric_name}
2. Return the value in a structured format
3. If the value is in millions or billions, convert to full number
4. For percentages, return the number without the % sign
5. If you cannot find the value, set found to false

Return your answer in this exact JSON format:
{{
    "found": true or false,
    "raw_value": "the exact text containing the number (e.g., '$394.3 billion')",
    "numeric_value": the number as a float (e.g., 394300000000),
    "confidence": your confidence from 0.0 to 1.0
}}

Only return the JSON, nothing else."""

        try:
            response = self.llm.invoke(extraction_prompt)
            response_text = response.content.strip()

            # Parse JSON from response
            # Handle potential markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]

            result = json.loads(response_text)

            return {
                'success': result.get('found', False),
                'value': result.get('numeric_value'),
                'raw_value': result.get('raw_value'),
                'confidence': result.get('confidence', 0.0)
            }

        except (json.JSONDecodeError, Exception) as e:
            # Fallback to regex extraction
            return self._fallback_extraction(answer, unit)

    def _fallback_extraction(self, text: str, unit: str) -> Dict[str, Any]:
        """
        Fallback regex-based extraction when LLM parsing fails.
        """
        # Patterns for different units
        if unit == 'dollars':
            # Match dollar amounts: $123.4 billion, $123,456,789, etc.
            patterns = [
                r'\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
                r'([\d,]+(?:\.\d+)?)\s*(billion|million)\s*(?:dollars)?',
            ]
        elif unit == 'percentage':
            patterns = [
                r'([-]?[\d.]+)\s*%',
                r'([-]?[\d.]+)\s*percent',
            ]
        elif unit == 'ratio':
            patterns = [
                r'([\d.]+)\s*(?:to\s*1|:1|x)?',
            ]
        else:
            patterns = [
                r'([\d,]+(?:\.\d+)?)',
            ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)

                    # Apply multiplier if present
                    if len(match.groups()) > 1 and match.group(2):
                        multiplier_text = match.group(2).lower()
                        if multiplier_text in ['billion', 'b']:
                            value *= 1e9
                        elif multiplier_text in ['million', 'm']:
                            value *= 1e6

                    return {
                        'success': True,
                        'value': value,
                        'raw_value': match.group(0),
                        'confidence': 0.6  # Lower confidence for regex extraction
                    }
                except ValueError:
                    continue

        return {
            'success': False,
            'value': None,
            'raw_value': None,
            'confidence': 0.0
        }

    def extract_multiple_metrics(self, metric_names: List[str], ticker: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract multiple metrics at once.

        Args:
            metric_names: List of metric names to extract
            ticker: Stock ticker

        Returns:
            Dict mapping metric names to their extraction results
        """
        results = {}
        for metric_name in metric_names:
            results[metric_name] = self.extract_metric(metric_name, ticker)
        return results

    def extract_standard_metrics(self, ticker: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract a standard set of key financial metrics.

        Returns all commonly used metrics for financial analysis.
        """
        standard_metrics = [
            'revenue',
            'net_income',
            'gross_profit',
            'operating_income',
            'operating_margin',
            'total_assets',
            'total_debt',
            'cash',
            'eps',
            'revenue_growth',
        ]
        return self.extract_multiple_metrics(standard_metrics, ticker)


# Test function
if __name__ == "__main__":
    print("Testing MetricExtractor...")

    extractor = MetricExtractor()

    # This test requires a filing to be indexed first
    # Run the SEC downloader and indexer before testing

    ticker = "AAPL"
    print(f"\nExtracting metrics for {ticker}...")

    # Test single metric extraction
    result = extractor.extract_metric("revenue", ticker)
    print(f"\nRevenue extraction:")
    print(f"  Success: {result['success']}")
    print(f"  Value: {result.get('value')}")
    print(f"  Raw: {result.get('raw_value')}")
    print(f"  Confidence: {result.get('confidence')}")

import os
from typing import Dict, Any
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()

class ExaService:
    def __init__(self):
        self.client = Exa(api_key=os.getenv('EXA_API_KEY'))
    
    async def get_metric(self, question: str) -> Dict[str, Any]:
        """Get a specific metric using Exa Answer API"""
        try:
            response = self.client.answer(question)
            return {
                'answer': response.answer,
                'citations': response.citations if hasattr(response, 'citations') else []
            }
        except Exception as e:
            print(f"Error getting metric: {e}")
            return {'answer': None, 'citations': []}
    
    def parse_numeric_value(self, text: str) -> float:
        """Extract numeric value from text response"""
        import re

        # First check if this is a failure message
        failure_indicators = [
        "cannot provide",
        "do not contain",
        "not available",
        "unable to",
        "sorry",
        "no specific"
        ]
        if any(indicator in text.lower() for indicator in failure_indicators):
             return None  # Return None, not 0.0!
        # Look for patterns like $1.5M, -23%, etc
        patterns = [
            r'\$?([\d,]+\.?\d*)\s*([BMK])?',  # Dollar amounts
            r'([-]?[\d\.]+)%',  # Percentages
            r'([-]?[\d\.]+)x?'  # Ratios
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
        if match:
            value = float(match.group(1).replace(',', ''))
            if len(match.groups()) > 1 and match.group(2):
                multiplier = {'K': 1e3, 'M': 1e6, 'B': 1e9}.get(match.group(2), 1)
                value *= multiplier
            return value
    
        return None  # Not 0.0!
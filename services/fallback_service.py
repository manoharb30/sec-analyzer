from typing import Dict, Any

class FallbackDataService:
    """Fallback data sources when Exa fails"""
    
    async def try_alternative_sources(self, ticker: str) -> Dict[str, Any]:
        """Try alternative data sources"""
        alternatives = {}
        
        # Try searching for company info first
        company_search = await self.search_company_info(ticker)
        if not company_search['found']:
            return {
                'status': 'not_found',
                'message': f"{ticker} may not be a valid ticker or the company may be private/delisted"
            }
        
        # Try simpler questions
        simplified_questions = [
            f"Is {ticker} profitable?",
            f"Is {ticker} growing revenue?",
            f"What industry is {ticker} in?"
        ]
        
        for question in simplified_questions:
            answer = await self.exa.answer(question)
            if answer:
                alternatives[question] = answer
        
        return alternatives
    
    async def search_company_info(self, ticker: str) -> Dict[str, Any]:
        """Verify if company exists and is public"""
        query = f"Is {ticker} a publicly traded company stock ticker?"
        result = await self.exa.answer(query)
        
        return {
            'found': result and 'yes' in result.lower(),
            'info': result
        }
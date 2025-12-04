import os
import asyncio
import aiohttp
from typing import List, Dict, Any
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()

class CerebrasSearchService:
    def __init__(self):
        self.client = Cerebras(api_key=os.getenv('CEREBRAS_API_KEY'))
        
    async def multi_angle_search(self, base_query: str) -> Dict[str, Any]:
        """
        Implement Cerebras-style multi-angle search
        Based on their Perplexity cookbook pattern
        """
        # Generate multiple search angles
        search_queries = self.generate_search_queries(base_query)
        
        # Execute searches in parallel
        search_results = await self.parallel_web_search(search_queries)
        
        # Synthesize results using LLM
        synthesis = await self.synthesize_results(base_query, search_results)
        
        return {
            'synthesis': synthesis,
            'sources': search_results,
            'confidence': self.calculate_confidence(search_results)
        }
    
    def generate_search_queries(self, base_query: str) -> List[str]:
        """Generate multiple search angles for comprehensive coverage"""
        return [
            base_query,
            f"{base_query} analysis 2024",
            f"{base_query} expert opinion",
            f"{base_query} SEC filing",
            f"{base_query} news recent"
        ]
    
    async def parallel_web_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple searches in parallel"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.web_search(session, q) for q in queries]
            results = await asyncio.gather(*tasks)
        return [r for r in results if r]
    
    async def web_search(self, session: aiohttp.ClientSession, query: str) -> Dict[str, Any]:
        """Execute a single web search (placeholder - implement with your preferred search API)"""
        # This is where you'd integrate with your search provider
        # For now, returning mock data
        return {
            'query': query,
            'results': f"Mock results for: {query}",
            'source': 'web'
        }
    
    async def synthesize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Use Cerebras LLM to synthesize multiple search results"""
        combined_results = "\n\n".join([r['results'] for r in results])
        
        prompt = f"""
        Query: {query}
        
        Search Results:
        {combined_results}
        
        Provide a concise synthesis of the key findings that answer the query.
        Focus on facts and cite sources where relevant.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b",
                messages=[
                    {"role": "system", "content": "You are a financial analyst synthesizing research."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Synthesis error: {e}")
            return "Unable to synthesize results"
    
    def calculate_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results"""
        if not results:
            return 0.0
        
        # Simple confidence: more results = higher confidence
        base_confidence = min(len(results) / 5, 1.0)
        
        # Adjust based on result quality (placeholder logic)
        quality_factor = 0.8  # Would analyze actual result quality
        
        return base_confidence * quality_factor
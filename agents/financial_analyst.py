import asyncio
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AnalysisState
from services.exa_service import ExaService
from services.cerebras_search_service import CerebrasSearchService
import logging

logger = logging.getLogger(__name__)

class FinancialAnalystAgent(BaseAgent):
    def __init__(self, ticker: str, **kwargs):
        super().__init__(ticker, **kwargs)
        self.exa = ExaService()
        self.cerebras = CerebrasSearchService()
        
    async def observe(self):
        logger.info(f"🔍 Observing {self.ticker}...")
    
        metrics_questions = [
        # (question, key_name, is_required)
        (f"What is {self.ticker} latest revenue from SEC filing?", "revenue", True),
        (f"What is {self.ticker} return on equity ROE?", "roe", True),
        (f"What is {self.ticker} debt-to-equity ratio?", "debt_equity", False),
        (f"What is {self.ticker} operating margin?", "operating_margin", False),
        (f"What is {self.ticker} revenue growth rate year over year?", "revenue_growth", True),
    ]
        critical_metrics_found = 0
        failed_metrics = []
    
        for question, key, is_required in metrics_questions:
         result = await self.exa.get_metric(question)
        
        if result['answer']:
            value = self.exa.parse_numeric_value(result['answer'])
            
            # Check if parsing actually found a value
            if value is not None:
                self.observations[key] = {
                    'value': value,
                    'raw': result['answer'],
                    'citations': result['citations']
                }
                if is_required:
                    critical_metrics_found += 1
            else:
                # Exa responded but couldn't provide the data
                logger.warning(f"⚠️ Exa cannot provide {key}: {result['answer'][:50]}")
                failed_metrics.append(key)
                if is_required:
                    logger.error(f"❌ Critical metric {key} unavailable")
        else:
            # No response at all
            failed_metrics.append(key)
            logger.error(f"❌ No response for {key}")
    
    # Strict validation - need at least 2 real metrics
        if critical_metrics_found < 2:
            logger.error(f"Cannot analyze {self.ticker}: Only {critical_metrics_found} metrics available")
            logger.error(f"Failed metrics: {failed_metrics}")
            self.state = AnalysisState.CONCLUDED
            self.confidence = 0.0
            self.failure_reason = f"insufficient_data: {', '.join(failed_metrics)}"
            return
    
        logger.info(f"📊 Valid observations: {list(self.observations.keys())}")
        self.state = AnalysisState.DECIDING
        
    async def decide(self):
        """Decide: Determine what needs deeper investigation"""
        logger.info("🤔 Analyzing observations to decide investigations...")
        
        self.decisions = []
        
        # Decision tree based on observations
        roe = self.observations.get('roe', {}).get('value', 0)
        if roe < 0:
            self.decisions.append({
                'area': 'profitability',
                'reason': 'negative_roe',
                'severity': 'high',
                'query': f"Why is {self.ticker} unprofitable losing money business model reasons"
            })
        
        revenue_growth = self.observations.get('revenue_growth', {}).get('value', 0)
        if revenue_growth < -10:
            self.decisions.append({
                'area': 'revenue',
                'reason': 'declining_revenue',
                'severity': 'high',
                'query': f"Why did {self.ticker} revenue decline strategic pivot or market issues"
            })
        
        debt_equity = self.observations.get('debt_equity', {}).get('value', 0)
        if debt_equity > 2:
            self.decisions.append({
                'area': 'leverage',
                'reason': 'high_debt',
                'severity': 'medium',
                'query': f"Is {self.ticker} debt level sustainable covenant risks bankruptcy"
            })
        
        margins = self.observations.get('margins', {}).get('value', 0)
        if margins < 10:
            self.decisions.append({
                'area': 'margins',
                'reason': 'low_margins',
                'severity': 'medium',
                'query': f"Why does {self.ticker} have low profit margins competition or costs"
            })
        
        # If no red flags, do general competitive analysis
        if not self.decisions:
            self.decisions.append({
                'area': 'competitive',
                'reason': 'standard_analysis',
                'severity': 'low',
                'query': f"What is {self.ticker} competitive position market share moat"
            })
        
        logger.info(f"📋 Made {len(self.decisions)} investigation decisions")
        self.state = AnalysisState.ACTING
        
    async def act(self):
        """Act: Execute investigations using Cerebras search pattern"""
        logger.info("🎯 Executing investigations...")
        
        # Execute all investigations in parallel
        tasks = [
            self.cerebras.multi_angle_search(decision['query'])
            for decision in self.decisions
        ]
        
        search_results = await asyncio.gather(*tasks)
        
        # Store results
        for decision, result in zip(self.decisions, search_results):
            self.actions_taken.append({
                'decision': decision,
                'findings': result['synthesis'],
                'sources': result['sources'],
                'confidence': result['confidence']
            })
        
        logger.info(f"✅ Completed {len(self.actions_taken)} investigations")
        self.state = AnalysisState.EVALUATING
        
    async def evaluate(self):
        """Evaluate: Assess if we have sufficient information"""
        logger.info("📊 Evaluating information completeness...")
        
        # Calculate overall confidence
        if self.actions_taken:
            confidences = [action['confidence'] for action in self.actions_taken]
            self.confidence = sum(confidences) / len(confidences)
        else:
            self.confidence = 0.0
        
        logger.info(f"🎯 Overall confidence: {self.confidence:.1%}")
        
        # Determine if we need more information
        if self.confidence < self.confidence_threshold:
            # Identify weak areas
            weak_areas = [
                action['decision']['area']
                for action in self.actions_taken
                if action['confidence'] < self.confidence_threshold
            ]
            
            if weak_areas and self.current_iteration < self.max_iterations - 1:
                logger.info(f"🔄 Need more information on: {weak_areas}")
                # Add follow-up investigations
                for area in weak_areas:
                    self.decisions.append({
                        'area': area,
                        'reason': 'insufficient_data',
                        'severity': 'low',
                        'query': f"More details on {self.ticker} {area} specific numbers"
                    })
                self.state = AnalysisState.ACTING
            else:
                # Accept current information
                self.state = AnalysisState.CONCLUDED
        else:
            # Sufficient information gathered
            self.state = AnalysisState.CONCLUDED
            
    def conclude(self) -> Dict[str, Any]:
        """Conclude: Generate final analysis or failure report"""

        # Handle failure cases
        if hasattr(self, 'failure_reason'):
            if self.failure_reason == "insufficient_data":
                return {
                    'ticker': self.ticker,
                    'status': 'failed',
                    'error': 'Unable to retrieve basic financial metrics',
                    'recommendation': 'UNABLE TO ANALYZE - Data unavailable',
                    'suggestions': [
                        f"Verify {self.ticker} is a valid US public company",
                        f"Check if {self.ticker} has filed recent SEC reports",
                        f"Try alternative ticker if company merged/renamed"
                    ],
                    'confidence': 0.0
                }

        # Normal analysis if data available
        logger.info("📝 Generating final analysis...")

        analysis = {
            'ticker': self.ticker,
            'metrics': self._format_metrics(),
            'insights': self._generate_insights(),
            'risks': self._identify_risks(),
            'opportunities': self._identify_opportunities(),
            'recommendation': self._generate_recommendation(),
            'confidence': self.confidence
        }

        return analysis
    
    def _format_metrics(self) -> Dict[str, Any]:
        """Format observed metrics for output"""
        formatted = {}
        for key, data in self.observations.items():
            formatted[key] = {
                'value': data['value'],
                'display': data['raw'],
                'citations': data['citations'][:2] if data['citations'] else []
            }
        return formatted
    
    def _generate_insights(self) -> List[str]:
        """Generate key insights from investigations"""
        insights = []
        
        for action in self.actions_taken:
            area = action['decision']['area']
            findings = action['findings']
            
            if area == 'profitability' and 'strategic' in findings.lower():
                insights.append(f"Losses appear strategic: {findings}")
            elif area == 'revenue' and 'pivot' in findings.lower():
                insights.append(f"Revenue decline due to business model shift: {findings}")
            elif area == 'leverage' and 'sustainable' in findings.lower():
                insights.append(f"Debt levels analyzed: {findings}")
            else:
                insights.append(f"{area.title()}: {findings}")
        
        return insights[:5]  # Top 5 insights
    
    def _identify_risks(self) -> List[str]:
        """Identify key risks from analysis"""
        risks = []
        
        for action in self.actions_taken:
            if action['decision']['severity'] == 'high':
                risks.append(f"{action['decision']['area'].title()} risk: {action['decision']['reason']}")
        
        return risks
    
    def _identify_opportunities(self) -> List[str]:
        """Identify opportunities from analysis"""
        opportunities = []
        
        for action in self.actions_taken:
            findings = action['findings'].lower()
            if any(word in findings for word in ['growth', 'expansion', 'increasing', 'opportunity']):
                opportunities.append(f"Potential in {action['decision']['area']}")
        
        return opportunities
    
    def _generate_recommendation(self) -> str:
        """Generate buy/hold/sell recommendation"""
        risk_count = len(self._identify_risks())
        opp_count = len(self._identify_opportunities())
        
        roe = self.observations.get('roe', {}).get('value', 0)
        revenue_growth = self.observations.get('revenue_growth', {}).get('value', 0)
        
        if self.confidence < 0.5:
            return "HOLD - Insufficient data for strong conviction"
        elif risk_count > opp_count + 1:
            return "SELL - Risks outweigh opportunities"
        elif opp_count > risk_count and revenue_growth > 10:
            return "BUY - Strong growth with manageable risks"
        elif roe > 15 and revenue_growth > 0:
            return "BUY - Solid fundamentals"
        else:
            return "HOLD - Balanced risk/reward profile"
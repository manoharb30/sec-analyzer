"""
Financial Analyst Agent
Uses ODAE (Observe-Decide-Act-Evaluate) pattern for financial analysis.

Now uses the proper data pipeline:
1. Download SEC filing from EDGAR
2. Index in Pinecone with smart chunking
3. Extract metrics via RAG + LLM
4. Make analysis decisions based on real data
"""

import asyncio
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AnalysisState
from services.metric_extractor import MetricExtractor
from services.cerebras_search_service import CerebrasSearchService
from tools.sec_downloader import SECDownloaderTool
from rag.pinecone_rag import SECFilingRAG
import logging

logger = logging.getLogger(__name__)


class FinancialAnalystAgent(BaseAgent):
    """
    Financial Analyst Agent using ODAE pattern.

    Proper data flow:
    1. OBSERVE: Download filing -> Index in Pinecone -> Extract metrics via RAG
    2. DECIDE: Analyze metrics to identify investigation areas
    3. ACT: Execute deep-dive investigations
    4. EVALUATE: Assess information completeness
    5. CONCLUDE: Generate investment recommendation
    """

    def __init__(self, ticker: str, filing_type: str = "10-K", **kwargs):
        super().__init__(ticker, **kwargs)
        self.filing_type = filing_type
        self.downloader = SECDownloaderTool()
        self.rag = None  # Lazy initialization
        self.metric_extractor = None  # Lazy initialization
        self.cerebras = CerebrasSearchService()
        self.filing_data = None

    def _get_rag(self) -> SECFilingRAG:
        """Lazy initialization of RAG."""
        if self.rag is None:
            self.rag = SECFilingRAG()
        return self.rag

    def _get_metric_extractor(self) -> MetricExtractor:
        """Lazy initialization of MetricExtractor."""
        if self.metric_extractor is None:
            self.metric_extractor = MetricExtractor(rag_instance=self._get_rag())
        return self.metric_extractor

    async def _download_and_index_filing(self) -> bool:
        """
        Step 1: Download SEC filing and index in Pinecone.
        This must happen before any metric extraction.
        """
        logger.info(f"Downloading {self.filing_type} for {self.ticker}...")

        # Download filing
        self.filing_data = self.downloader._run(self.ticker, self.filing_type)

        if not self.filing_data.get('success'):
            logger.error(f"Failed to download filing: {self.filing_data.get('error')}")
            return False

        logger.info(f"Downloaded {self.filing_data.get('full_text_length', 0)} chars")
        logger.info(f"Company: {self.filing_data.get('company_name')}")
        logger.info(f"Filing Date: {self.filing_data.get('filing_date')}")

        # Index in Pinecone
        logger.info("Indexing filing in Pinecone...")
        rag = self._get_rag()
        index_result = rag.index_filing(
            filing_text=self.filing_data['full_text'],
            ticker=self.ticker,
            filing_type=self.filing_type,
            filing_date=self.filing_data.get('filing_date', 'unknown')
        )

        if not index_result.get('success'):
            logger.error(f"Failed to index filing: {index_result.get('error')}")
            return False

        logger.info(f"Indexed {index_result.get('chunks_indexed')} chunks")
        logger.info(f"Tables preserved: {index_result.get('tables_preserved', 0)}")
        logger.info(f"Sections: {index_result.get('sections_indexed', {})}")

        return True

    async def observe(self):
        """
        OBSERVE phase: Gather financial metrics from the SEC filing.

        1. Download and index the filing (if not already done)
        2. Extract key financial metrics using RAG
        3. Store observations for decision making
        """
        logger.info(f"Observing {self.ticker}...")

        # Step 1: Ensure filing is downloaded and indexed
        if self.filing_data is None:
            success = await self._download_and_index_filing()
            if not success:
                self.state = AnalysisState.CONCLUDED
                self.confidence = 0.0
                self.failure_reason = "filing_download_failed"
                return

        # Step 2: Extract metrics using RAG
        logger.info("Extracting financial metrics via RAG...")
        extractor = self._get_metric_extractor()

        # Define metrics to extract
        metrics_to_extract = [
            ('revenue', True),  # (metric_name, is_required)
            ('net_income', True),
            ('operating_margin', False),
            ('gross_margin', False),
            ('revenue_growth', True),
            ('eps', False),
            ('total_debt', False),
            ('cash', False),
            ('roe', False),
        ]

        critical_metrics_found = 0
        failed_metrics = []

        for metric_name, is_required in metrics_to_extract:
            logger.info(f"  Extracting {metric_name}...")
            result = extractor.extract_metric(metric_name, self.ticker)

            if result.get('success') and result.get('value') is not None:
                self.observations[metric_name] = {
                    'value': result['value'],
                    'raw': result.get('raw_value', str(result['value'])),
                    'confidence': result.get('confidence', 0.0),
                    'section': result.get('source_section', 'unknown')
                }
                logger.info(f"    {metric_name}: {result.get('raw_value')} (confidence: {result.get('confidence', 0):.2f})")

                if is_required:
                    critical_metrics_found += 1
            else:
                failed_metrics.append(metric_name)
                logger.warning(f"    {metric_name}: Not found")

        # Step 3: Validate we have enough data
        if critical_metrics_found < 2:
            logger.error(f"Insufficient data: Only {critical_metrics_found} critical metrics found")
            logger.error(f"Failed metrics: {failed_metrics}")
            self.state = AnalysisState.CONCLUDED
            self.confidence = 0.0
            self.failure_reason = f"insufficient_data: {', '.join(failed_metrics)}"
            return

        logger.info(f"Successfully extracted {len(self.observations)} metrics")
        self.state = AnalysisState.DECIDING

    async def decide(self):
        """
        DECIDE phase: Analyze observations to determine investigation areas.
        """
        logger.info("Analyzing observations to decide investigations...")

        self.decisions = []

        # Decision tree based on extracted metrics

        # Check profitability
        net_income = self.observations.get('net_income', {}).get('value', 0)
        if net_income and net_income < 0:
            self.decisions.append({
                'area': 'profitability',
                'reason': 'negative_net_income',
                'severity': 'high',
                'query': f"Why is {self.ticker} unprofitable? What are the main cost drivers?"
            })

        # Check revenue growth
        revenue_growth = self.observations.get('revenue_growth', {}).get('value', 0)
        if revenue_growth and revenue_growth < -10:
            self.decisions.append({
                'area': 'revenue',
                'reason': 'declining_revenue',
                'severity': 'high',
                'query': f"Why is {self.ticker} revenue declining? Is this a strategic pivot or market issue?"
            })
        elif revenue_growth and revenue_growth > 20:
            self.decisions.append({
                'area': 'growth',
                'reason': 'strong_growth',
                'severity': 'low',
                'query': f"What is driving {self.ticker}'s strong revenue growth? Is it sustainable?"
            })

        # Check margins
        operating_margin = self.observations.get('operating_margin', {}).get('value', 0)
        if operating_margin and operating_margin < 5:
            self.decisions.append({
                'area': 'margins',
                'reason': 'low_margins',
                'severity': 'medium',
                'query': f"Why does {self.ticker} have low operating margins? What is the industry average?"
            })

        # Check debt levels
        total_debt = self.observations.get('total_debt', {}).get('value', 0)
        cash = self.observations.get('cash', {}).get('value', 0)
        if total_debt and cash and total_debt > cash * 3:
            self.decisions.append({
                'area': 'leverage',
                'reason': 'high_debt',
                'severity': 'medium',
                'query': f"Is {self.ticker}'s debt level sustainable? What are the covenant risks?"
            })

        # If no red flags, do standard competitive analysis
        if not self.decisions:
            self.decisions.append({
                'area': 'competitive',
                'reason': 'standard_analysis',
                'severity': 'low',
                'query': f"What is {self.ticker}'s competitive position and market share?"
            })

        logger.info(f"Made {len(self.decisions)} investigation decisions")
        for d in self.decisions:
            logger.info(f"  - {d['area']} ({d['severity']}): {d['reason']}")

        self.state = AnalysisState.ACTING

    async def act(self):
        """
        ACT phase: Execute investigations.

        Uses RAG for filing-based queries and Cerebras for broader market research.
        """
        logger.info("Executing investigations...")

        rag = self._get_rag()

        for decision in self.decisions:
            logger.info(f"  Investigating: {decision['area']}...")

            # First, try to get more context from the filing via RAG
            rag_result = rag.query(
                question=decision['query'],
                ticker=self.ticker,
                top_k=5
            )

            # Then, do broader search for market context
            search_result = await self.cerebras.multi_angle_search(decision['query'])

            # Combine findings
            filing_context = rag_result.get('answer', '') if rag_result.get('success') else ''
            market_context = search_result.get('synthesis', '')

            combined_findings = f"From SEC Filing: {filing_context}\n\nMarket Context: {market_context}"

            self.actions_taken.append({
                'decision': decision,
                'findings': combined_findings,
                'filing_sources': rag_result.get('sections_searched', []),
                'market_sources': search_result.get('sources', []),
                'confidence': search_result.get('confidence', 0.5)
            })

        logger.info(f"Completed {len(self.actions_taken)} investigations")
        self.state = AnalysisState.EVALUATING

    async def evaluate(self):
        """
        EVALUATE phase: Assess if we have sufficient information.
        """
        logger.info("Evaluating information completeness...")

        # Calculate overall confidence
        if self.actions_taken:
            # Weight by number of metrics and investigation quality
            metric_confidence = len(self.observations) / 9.0  # 9 possible metrics
            investigation_confidences = [action['confidence'] for action in self.actions_taken]
            avg_investigation_confidence = sum(investigation_confidences) / len(investigation_confidences)

            self.confidence = 0.6 * metric_confidence + 0.4 * avg_investigation_confidence
        else:
            self.confidence = len(self.observations) / 9.0

        logger.info(f"Overall confidence: {self.confidence:.1%}")

        # Determine if we need more information
        if self.confidence < self.confidence_threshold and self.current_iteration < self.max_iterations - 1:
            weak_areas = [
                action['decision']['area']
                for action in self.actions_taken
                if action['confidence'] < self.confidence_threshold
            ]

            if weak_areas:
                logger.info(f"Need more information on: {weak_areas}")
                # Add follow-up investigations
                for area in weak_areas[:2]:  # Limit to 2 follow-ups
                    self.decisions.append({
                        'area': area,
                        'reason': 'insufficient_data',
                        'severity': 'low',
                        'query': f"More specific details on {self.ticker} {area} with numbers"
                    })
                self.state = AnalysisState.ACTING
                return

        self.state = AnalysisState.CONCLUDED

    def conclude(self) -> Dict[str, Any]:
        """
        CONCLUDE phase: Generate final analysis and recommendation.
        """
        # Handle failure cases
        if hasattr(self, 'failure_reason') and self.failure_reason:
            if 'filing_download_failed' in self.failure_reason:
                return {
                    'ticker': self.ticker,
                    'status': 'failed',
                    'error': 'Could not download SEC filing',
                    'recommendation': 'UNABLE TO ANALYZE',
                    'suggestions': [
                        f"Verify {self.ticker} is a valid US public company",
                        f"Check if {self.ticker} has filed recent SEC reports",
                        "Try an alternative ticker if company merged/renamed"
                    ],
                    'confidence': 0.0
                }
            elif 'insufficient_data' in self.failure_reason:
                return {
                    'ticker': self.ticker,
                    'status': 'failed',
                    'error': 'Unable to extract sufficient financial metrics',
                    'recommendation': 'UNABLE TO ANALYZE - Insufficient data',
                    'suggestions': [
                        "The SEC filing may have unusual formatting",
                        "Try re-indexing the filing",
                        "Check if the filing contains standard financial statements"
                    ],
                    'confidence': 0.0
                }

        # Generate successful analysis
        logger.info("Generating final analysis...")

        analysis = {
            'ticker': self.ticker,
            'status': 'success',
            'company_name': self.filing_data.get('company_name') if self.filing_data else self.ticker,
            'filing_type': self.filing_type,
            'filing_date': self.filing_data.get('filing_date') if self.filing_data else None,
            'metrics': self._format_metrics(),
            'insights': self._generate_insights(),
            'risks': self._identify_risks(),
            'opportunities': self._identify_opportunities(),
            'recommendation': self._generate_recommendation(),
            'confidence': self.confidence
        }

        return analysis

    def _format_metrics(self) -> Dict[str, Any]:
        """Format extracted metrics for output."""
        formatted = {}
        for key, data in self.observations.items():
            formatted[key] = {
                'value': data['value'],
                'display': data['raw'],
                'confidence': data.get('confidence', 0),
                'section': data.get('section', 'unknown')
            }
        return formatted

    def _generate_insights(self) -> List[str]:
        """Generate key insights from investigations."""
        insights = []

        for action in self.actions_taken:
            area = action['decision']['area']
            findings = action['findings']

            # Truncate findings for display
            findings_summary = findings[:300] + "..." if len(findings) > 300 else findings

            if area == 'profitability':
                insights.append(f"Profitability Analysis: {findings_summary}")
            elif area == 'growth':
                insights.append(f"Growth Drivers: {findings_summary}")
            elif area == 'margins':
                insights.append(f"Margin Analysis: {findings_summary}")
            elif area == 'leverage':
                insights.append(f"Debt Analysis: {findings_summary}")
            else:
                insights.append(f"{area.title()}: {findings_summary}")

        return insights[:5]

    def _identify_risks(self) -> List[str]:
        """Identify key risks from analysis."""
        risks = []

        for action in self.actions_taken:
            if action['decision']['severity'] == 'high':
                risks.append(
                    f"{action['decision']['area'].title()} Risk: {action['decision']['reason'].replace('_', ' ')}"
                )

        # Add metric-based risks
        if self.observations.get('revenue_growth', {}).get('value', 0) < 0:
            risks.append("Revenue Decline Risk: Negative revenue growth trend")

        if self.observations.get('operating_margin', {}).get('value', 100) < 5:
            risks.append("Margin Pressure Risk: Low operating margins")

        return risks

    def _identify_opportunities(self) -> List[str]:
        """Identify opportunities from analysis."""
        opportunities = []

        # Check for positive signals
        revenue_growth = self.observations.get('revenue_growth', {}).get('value', 0)
        if revenue_growth and revenue_growth > 15:
            opportunities.append(f"Strong Growth: {revenue_growth:.1f}% revenue growth")

        operating_margin = self.observations.get('operating_margin', {}).get('value', 0)
        if operating_margin and operating_margin > 20:
            opportunities.append(f"High Margins: {operating_margin:.1f}% operating margin")

        # Check investigation findings for positive mentions
        for action in self.actions_taken:
            findings_lower = action['findings'].lower()
            if any(word in findings_lower for word in ['growth', 'expansion', 'increasing', 'opportunity', 'market leader']):
                opportunities.append(f"Potential in {action['decision']['area']}")

        return opportunities[:5]

    def _generate_recommendation(self) -> str:
        """Generate BUY/HOLD/SELL recommendation."""
        risks = self._identify_risks()
        opportunities = self._identify_opportunities()

        # Get key metrics
        revenue_growth = self.observations.get('revenue_growth', {}).get('value', 0) or 0
        net_income = self.observations.get('net_income', {}).get('value', 0) or 0
        operating_margin = self.observations.get('operating_margin', {}).get('value', 0) or 0

        # Decision logic
        if self.confidence < 0.4:
            return "HOLD - Insufficient data for strong conviction"

        high_risk_count = sum(1 for r in risks if 'High' in r or 'Decline' in r)
        opportunity_count = len(opportunities)

        if high_risk_count >= 2:
            return "SELL - Multiple significant risk factors identified"
        elif net_income < 0 and revenue_growth < 0:
            return "SELL - Unprofitable with declining revenue"
        elif revenue_growth > 15 and operating_margin > 15:
            return "BUY - Strong growth with healthy margins"
        elif revenue_growth > 10 and net_income > 0:
            return "BUY - Positive growth trajectory with profitability"
        elif opportunity_count > high_risk_count + 1:
            return "BUY - Opportunities outweigh risks"
        elif high_risk_count > opportunity_count:
            return "SELL - Risks outweigh opportunities"
        else:
            return "HOLD - Balanced risk/reward profile"

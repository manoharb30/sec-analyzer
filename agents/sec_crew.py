"""
SEC Filing Analysis Crew
Multi-agent system for analyzing SEC 10-K/10-Q filings using RAG
"""

import os
import sys
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.pinecone_rag import SECFilingRAG


class SECQueryTool(BaseTool):
    """Tool for agents to query SEC filing sections via RAG"""
    name: str = "query_sec_filing"
    description: str = """Query the SEC filing to find specific information.
    Use this to search for financial metrics, risk factors, business descriptions, etc.
    Input should be a specific question about the filing."""

    rag: Any = Field(default=None, exclude=True)
    ticker: str = Field(default="")

    def _run(self, query: str) -> str:
        """Query the RAG system for relevant filing sections"""
        if not self.rag:
            return "Error: RAG system not initialized"

        result = self.rag.query(
            question=query,
            ticker=self.ticker,
            top_k=8  # Get more chunks for better context
        )

        if not result.get("success"):
            return f"Query failed: {result.get('error', 'Unknown error')}"

        # Return the answer - the RAG already processes and extracts info
        answer = result.get("answer", "No answer found")

        # Add section info
        sections = result.get("sections_searched", [])
        if sections:
            answer += f"\n\n(Searched sections: {', '.join(sections)})"

        return answer


class SECAnalysisCrew:
    """Crew for analyzing SEC filings with multiple specialized agents using RAG"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Fast and high rate limits
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.rag = SECFilingRAG()
        self._ticker = ""
        self._filing_indexed = False

    def _index_filing(self, filing_text: str, ticker: str, filing_type: str) -> bool:
        """Index the filing in Pinecone for RAG queries"""
        try:
            result = self.rag.index_filing(
                filing_text=filing_text,
                ticker=ticker,
                filing_type=filing_type,
                filing_date="latest"
            )
            self._filing_indexed = result.get("success", False)
            return self._filing_indexed
        except Exception as e:
            print(f"Failed to index filing: {e}")
            return False

    def _create_query_tool(self) -> SECQueryTool:
        """Create a query tool for agents to use"""
        tool = SECQueryTool()
        tool.rag = self.rag
        tool.ticker = self._ticker
        return tool

    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents for SEC analysis with RAG tools"""

        query_tool = self._create_query_tool()

        financial_researcher = Agent(
            role="Financial Researcher",
            goal="Extract key financial metrics and business data from SEC filings using the query tool",
            backstory="""You are an expert financial analyst with 15+ years of experience
            analyzing SEC filings. You specialize in identifying key financial metrics,
            revenue trends, profit margins, and cash flow patterns.
            IMPORTANT: Use the query_sec_filing tool to search for specific financial data.
            Make multiple queries for: revenue, net income, gross margin, operating income,
            cash flow, debt, and segment breakdowns.""",
            llm=self.llm,
            tools=[query_tool],
            verbose=True,
            allow_delegation=False
        )

        risk_analyst = Agent(
            role="Risk Analyst",
            goal="Identify and assess key risk factors using the query tool",
            backstory="""You are a senior risk analyst who specializes in evaluating
            corporate risk disclosures. Use the query_sec_filing tool to search for
            risk factors, legal proceedings, and material uncertainties.
            Query for: "risk factors", "legal proceedings", "material risks",
            "regulatory risks", "competition risks".""",
            llm=self.llm,
            tools=[query_tool],
            verbose=True,
            allow_delegation=False
        )

        business_analyst = Agent(
            role="Business Strategy Analyst",
            goal="Analyze business model and competitive position using the query tool",
            backstory="""You are a strategy consultant who analyzes companies' competitive
            positions. Use the query_sec_filing tool to search for business description,
            products, services, competition, and strategic initiatives.
            Query for: "business description", "products and services", "competition",
            "growth strategy", "market position".""",
            llm=self.llm,
            tools=[query_tool],
            verbose=True,
            allow_delegation=False
        )

        report_writer = Agent(
            role="Investment Report Writer",
            goal="Synthesize analysis into a comprehensive investment report",
            backstory="""You are an expert investment writer who creates clear, actionable
            reports. You synthesize the financial, risk, and business analyses from
            other agents into a cohesive investment summary. Include specific numbers
            and cite sources where available.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        return {
            "financial_researcher": financial_researcher,
            "risk_analyst": risk_analyst,
            "business_analyst": business_analyst,
            "report_writer": report_writer
        }

    def _create_tasks(self, agents: Dict[str, Agent], ticker: str) -> list:
        """Create analysis tasks for the crew - agents use RAG tool to query filing"""

        financial_task = Task(
            description=f"""Analyze the {ticker} SEC filing and extract SPECIFIC financial metrics.

            USE THE query_sec_filing TOOL to search for financial data. Make these queries:
            1. "What is the total revenue and revenue growth?"
            2. "What is the net income and profit margin?"
            3. "What is the gross profit and gross margin?"
            4. "What is the operating income and operating margin?"
            5. "What is the total cash and cash equivalents?"
            6. "What is the total debt?"
            7. "What is the free cash flow?"
            8. "What are the revenue breakdowns by segment?"

            FORMAT YOUR OUTPUT AS A TABLE with actual numbers from the filing.""",
            expected_output="""A structured financial analysis with:
            - Key Financial Metrics TABLE with actual dollar amounts and percentages
            - Revenue breakdown by segment
            - Profitability metrics
            - Cash flow summary
            - All metrics must have REAL NUMBERS from the filing""",
            agent=agents["financial_researcher"]
        )

        risk_task = Task(
            description=f"""Analyze the risk factors from the {ticker} SEC filing.

            USE THE query_sec_filing TOOL to search for risks. Make these queries:
            1. "What are the main risk factors?"
            2. "What are the legal proceedings and litigation risks?"
            3. "What are the regulatory and compliance risks?"
            4. "What are the market and competition risks?"
            5. "What are the operational and supply chain risks?"

            Identify the TOP 5 most material risks and assess their impact.""",
            expected_output="""A risk assessment with:
            - Top 5 material risks with categories
            - Impact assessment (High/Medium/Low) for each
            - Brief description of each risk""",
            agent=agents["risk_analyst"]
        )

        business_task = Task(
            description=f"""Analyze the business strategy and competitive position of {ticker}.

            USE THE query_sec_filing TOOL to search for business info. Make these queries:
            1. "What is the company's business description and model?"
            2. "What are the main products and services?"
            3. "Who are the main competitors?"
            4. "What are the growth strategies and initiatives?"
            5. "What are the competitive advantages?"

            Summarize the company's market position and strategic direction.""",
            expected_output="""A business analysis with:
            - Business model summary
            - Key products and services
            - Competitive advantages
            - Growth strategy highlights
            - Market position assessment""",
            agent=agents["business_analyst"]
        )

        synthesis_task = Task(
            description=f"""Create a comprehensive investment summary for {ticker} by synthesizing
            the financial, risk, and business analyses from the other agents.

            The report MUST include:

            1. **Executive Summary** (2-3 paragraphs)
               - Include key metrics: Revenue, Net Income, Growth Rate
               - Mention the company's market position

            2. **Financial Highlights**
               - Total Revenue, Net Income, Operating Margin %
               - Free Cash Flow, Cash Position, Debt
               - Use the ACTUAL NUMBERS from the financial analysis

            3. **Business Overview**
               - Key products/segments
               - Competitive advantages

            4. **Risk Assessment**
               - Top 3-5 risks with severity (High/Medium/Low)
               - Brief impact description

            5. **Key Takeaways** (5-7 bullet points)
               - Investment thesis points with supporting numbers

            Use the data provided by the other agents. Include specific numbers.""",
            expected_output="""A professional investment report with:
            - Executive Summary with key metrics
            - Financial Highlights with actual $ amounts and %
            - Business Overview with segment breakdown
            - Risk Assessment with severity ratings
            - Key Takeaways with supporting data""",
            agent=agents["report_writer"],
            context=[financial_task, risk_task, business_task]
        )

        return [financial_task, risk_task, business_task, synthesis_task]

    def analyze(self, filing_text: str, ticker: str, filing_type: str = "10-K") -> Dict[str, Any]:
        """
        Run the multi-agent analysis on an SEC filing using RAG

        Args:
            filing_text: The extracted text from the SEC filing
            ticker: Stock ticker symbol
            filing_type: Type of filing (10-K or 10-Q)

        Returns:
            Dictionary with analysis results
        """
        self._ticker = ticker

        # Step 1: Index the filing in Pinecone for RAG queries
        print(f"Indexing {ticker} filing in Pinecone...")
        if not self._index_filing(filing_text, ticker, filing_type):
            return {
                "success": False,
                "ticker": ticker,
                "error": "Failed to index filing in Pinecone"
            }
        print(f"Successfully indexed {ticker} filing")

        # Step 2: Create agents with RAG tools
        agents = self._create_agents()

        # Step 3: Create tasks (no filing text needed - agents query via RAG)
        tasks = self._create_tasks(agents, ticker)

        # Step 4: Run the crew
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        try:
            print(f"Starting multi-agent analysis for {ticker}...")
            result = crew.kickoff()

            return {
                "success": True,
                "ticker": ticker,
                "filing_type": filing_type,
                "analysis": str(result),
                "agents_used": list(agents.keys())
            }
        except Exception as e:
            return {
                "success": False,
                "ticker": ticker,
                "error": str(e)
            }


# Test function
if __name__ == "__main__":
    from tools.sec_downloader import SECDownloaderTool

    print("Testing SEC Analysis Crew...")

    # First download a filing
    downloader = SECDownloaderTool()
    filing = downloader._run("AAPL", "10-K")

    if not filing.get("success"):
        print(f"Failed to download filing: {filing.get('error')}")
        exit(1)

    print(f"Downloaded {filing['ticker']} {filing['filing_type']}")
    print(f"Filing length: {filing['full_text_length']} chars")

    # Run analysis
    crew = SECAnalysisCrew()
    result = crew.analyze(
        filing_text=filing["full_text"],
        ticker=filing["ticker"],
        filing_type=filing["filing_type"]
    )

    print("\n" + "=" * 50)
    print("ANALYSIS RESULT:")
    print("=" * 50)

    if result["success"]:
        print(result["analysis"])
    else:
        print(f"Analysis failed: {result['error']}")

"""
SEC Filing Analyzer API
FastAPI backend for SEC filing analysis with multi-agent system
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Import our modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sec_downloader import SECDownloaderTool
from agents.direct_analyzer import SECAnalysisCrew, DirectSECAnalyzer  # Use direct analyzer instead of CrewAI
from rag.pinecone_rag import SECFilingRAG

# Initialize FastAPI app
app = FastAPI(
    title="SEC Filing Analyzer",
    description="Multi-agent system for analyzing SEC 10-K/10-Q filings",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (lazy initialization for RAG)
downloader = SECDownloaderTool()
_rag = None

def get_rag():
    """Lazy initialization of RAG to handle missing API keys gracefully"""
    global _rag
    if _rag is None:
        _rag = SECFilingRAG()
    return _rag

# In-memory storage for analysis jobs (use Redis in production)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class AnalyzeRequest(BaseModel):
    ticker: str
    filing_type: str = "10-K"


class QuestionRequest(BaseModel):
    ticker: str
    question: str


class AnalysisResponse(BaseModel):
    job_id: str
    ticker: str
    status: str
    message: str


class AnalysisResult(BaseModel):
    ticker: str
    filing_type: str
    filing_date: Optional[str]
    company_name: Optional[str]
    analysis: Optional[str]
    status: str
    error: Optional[str] = None


class QuestionResponse(BaseModel):
    question: str
    answer: str
    ticker: str
    sources: list


# Background task for analysis
async def run_analysis(job_id: str, ticker: str, filing_type: str):
    """Run the full analysis pipeline in background"""
    try:
        # Update status
        analysis_jobs[job_id]["status"] = "downloading"

        # Step 1: Download filing
        filing = downloader._run(ticker, filing_type)

        if not filing.get("success"):
            analysis_jobs[job_id]["status"] = "failed"
            analysis_jobs[job_id]["error"] = filing.get("error", "Failed to download filing")
            return

        analysis_jobs[job_id]["filing_date"] = filing.get("filing_date")
        analysis_jobs[job_id]["company_name"] = filing.get("company_name")
        analysis_jobs[job_id]["filing_url"] = filing.get("filing_url")
        analysis_jobs[job_id]["status"] = "indexing"

        # Step 2: Index in Pinecone for RAG
        index_result = get_rag().index_filing(
            filing_text=filing["full_text"],
            ticker=ticker,
            filing_type=filing_type,
            filing_date=filing.get("filing_date", "unknown")
        )

        if not index_result.get("success"):
            analysis_jobs[job_id]["status"] = "failed"
            analysis_jobs[job_id]["error"] = index_result.get("error", "Failed to index filing")
            return

        analysis_jobs[job_id]["chunks_indexed"] = index_result.get("chunks_indexed")
        analysis_jobs[job_id]["status"] = "analyzing"

        # Step 3: Run multi-agent analysis
        crew = SECAnalysisCrew()
        analysis_result = crew.analyze(
            filing_text=filing["full_text"],
            ticker=ticker,
            filing_type=filing_type
        )

        if analysis_result.get("success"):
            analysis_jobs[job_id]["status"] = "completed"
            analysis_jobs[job_id]["analysis"] = analysis_result.get("analysis")
        else:
            analysis_jobs[job_id]["status"] = "failed"
            analysis_jobs[job_id]["error"] = analysis_result.get("error", "Analysis failed")

    except Exception as e:
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error"] = str(e)


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SEC Filing Analyzer",
        "version": "1.0.0"
    }


@app.post("/analyze")
async def analyze_filing(request: AnalyzeRequest):
    """
    Synchronous analysis of an SEC filing - downloads, analyzes, returns results

    - **ticker**: Stock ticker symbol (e.g., AAPL, MSFT)
    - **filing_type**: 10-K (annual) or 10-Q (quarterly)
    """
    ticker = request.ticker.upper()

    try:
        # Step 1: Download filing
        filing = downloader._run(ticker, request.filing_type)

        if not filing.get("success"):
            raise HTTPException(
                status_code=400,
                detail=filing.get("error", "Failed to download filing")
            )

        # Step 2: Run multi-agent analysis
        crew = SECAnalysisCrew()
        analysis_result = crew.analyze(
            filing_text=filing["full_text"],
            ticker=ticker,
            filing_type=request.filing_type
        )

        if not analysis_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=analysis_result.get("error", "Analysis failed")
            )

        # Step 3: Index in Pinecone for RAG (background)
        try:
            get_rag().index_filing(
                filing_text=filing["full_text"],
                ticker=ticker,
                filing_type=request.filing_type,
                filing_date=filing.get("filing_date", "unknown")
            )
        except Exception as e:
            print(f"RAG indexing failed (non-critical): {e}")

        # Return in format expected by frontend
        return {
            "ticker": ticker,
            "companyName": filing.get("company_name", ticker),
            "company_name": filing.get("company_name", ticker),
            "content": analysis_result.get("analysis", ""),
            "analysis": analysis_result.get("analysis", ""),
            "filing_date": filing.get("filing_date"),
            "filing_url": filing.get("filing_url"),
            "metrics": None  # Metrics extraction would be a separate enhancement
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/stream")
async def analyze_stream(ticker: str, filing_type: str = "10-K"):
    """
    SSE endpoint for streaming analysis progress.

    - **ticker**: Stock ticker symbol (e.g., AAPL, MSFT)
    - **filing_type**: 10-K (annual) or 10-Q (quarterly)

    Returns Server-Sent Events with progress updates.
    """
    ticker = ticker.upper()

    async def generate_events():
        try:
            # Step 1: Download filing with progress
            yield f"data: {json.dumps({'step': 'downloading', 'progress': 5, 'message': f'Downloading {ticker} {filing_type} from SEC EDGAR...'})}\n\n"
            await asyncio.sleep(0)  # Flush

            # Run download in thread to not block
            filing = await asyncio.get_event_loop().run_in_executor(
                None, lambda: downloader._run(ticker, filing_type)
            )

            if not filing.get("success"):
                yield f"data: {json.dumps({'step': 'error', 'progress': 100, 'error': filing.get('error', 'Failed to download filing')})}\n\n"
                return

            company_name = filing.get("company_name", ticker)
            yield f"data: {json.dumps({'step': 'downloaded', 'progress': 10, 'message': f'Downloaded {company_name} filing'})}\n\n"
            await asyncio.sleep(0)  # Flush

            # Step 2: Run streaming analysis in thread
            analyzer = DirectSECAnalyzer()

            # Create a queue for progress events
            import queue
            progress_queue = queue.Queue()
            analysis_done = False
            analysis_error = None

            def run_analysis():
                nonlocal analysis_done, analysis_error
                try:
                    for event in analyzer.analyze_with_progress(
                        filing_text=filing["full_text"],
                        ticker=ticker,
                        filing_type=filing_type
                    ):
                        progress_queue.put(event)
                except Exception as e:
                    analysis_error = str(e)
                finally:
                    analysis_done = True

            # Start analysis in background thread
            import threading
            analysis_thread = threading.Thread(target=run_analysis, daemon=True)
            analysis_thread.start()

            # Stream progress events as they come
            while not analysis_done or not progress_queue.empty():
                try:
                    progress_event = progress_queue.get(timeout=0.5)

                    # Transform result for frontend
                    if progress_event.get("step") == "complete":
                        result = progress_event.get("result", {})
                        final_data = {
                            "step": "complete",
                            "progress": 100,
                            "message": "Analysis complete",
                            "result": {
                                "ticker": ticker,
                                "companyName": filing.get("company_name", ticker),
                                "company_name": filing.get("company_name", ticker),
                                "content": result.get("analysis", ""),
                                "analysis": result.get("analysis", ""),
                                "filing_date": filing.get("filing_date"),
                                "filing_url": filing.get("filing_url"),
                                "metrics": None
                            }
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                    elif progress_event.get("step") == "error":
                        yield f"data: {json.dumps(progress_event)}\n\n"
                    else:
                        yield f"data: {json.dumps(progress_event)}\n\n"

                    await asyncio.sleep(0)  # Flush immediately

                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

            # Check for errors
            if analysis_error:
                yield f"data: {json.dumps({'step': 'error', 'progress': 100, 'error': analysis_error})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'progress': 100, 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/analyze/async", response_model=AnalysisResponse)
async def analyze_filing_async(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Start async analysis of an SEC filing (returns immediately)

    - **ticker**: Stock ticker symbol (e.g., AAPL, MSFT)
    - **filing_type**: 10-K (annual) or 10-Q (quarterly)
    """
    ticker = request.ticker.upper()
    job_id = f"{ticker}_{request.filing_type}"

    # Initialize job
    analysis_jobs[job_id] = {
        "ticker": ticker,
        "filing_type": request.filing_type,
        "status": "queued",
        "analysis": None,
        "error": None,
        "filing_date": None,
        "company_name": None
    }

    # Start background analysis
    background_tasks.add_task(run_analysis, job_id, ticker, request.filing_type)

    return AnalysisResponse(
        job_id=job_id,
        ticker=ticker,
        status="queued",
        message=f"Analysis started for {ticker} {request.filing_type}"
    )


@app.get("/analysis/{job_id}", response_model=AnalysisResult)
async def get_analysis(job_id: str):
    """Get the status/result of an analysis job"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]
    return AnalysisResult(
        ticker=job["ticker"],
        filing_type=job["filing_type"],
        filing_date=job.get("filing_date"),
        company_name=job.get("company_name"),
        analysis=job.get("analysis"),
        status=job["status"],
        error=job.get("error")
    )


@app.post("/question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a follow-up question about an indexed filing

    - **ticker**: Stock ticker to query
    - **question**: Your question about the filing
    """
    ticker = request.ticker.upper()

    result = get_rag().query(
        question=request.question,
        ticker=ticker
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to process question")
        )

    return QuestionResponse(
        question=request.question,
        answer=result["answer"],
        ticker=ticker,
        sources=result.get("sources", [])
    )


@app.get("/suggested-questions/{ticker}")
async def get_suggested_questions(ticker: str):
    """Get suggested follow-up questions for a ticker"""
    return {
        "ticker": ticker.upper(),
        "questions": get_rag().get_suggested_questions(ticker.upper())
    }


@app.get("/jobs")
async def list_jobs():
    """List all analysis jobs"""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "ticker": job["ticker"],
                "status": job["status"],
                "filing_type": job["filing_type"]
            }
            for job_id, job in analysis_jobs.items()
        ]
    }


@app.delete("/filing/{ticker}")
async def delete_filing(ticker: str):
    """Delete indexed data for a ticker"""
    result = get_rag().delete_filing(ticker.upper())
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

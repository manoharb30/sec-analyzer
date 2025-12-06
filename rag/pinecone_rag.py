"""
Pinecone RAG for SEC Filing Follow-up Questions
Stores filing chunks in Pinecone for retrieval-augmented generation
Uses smart chunking to preserve financial tables and section context
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class SECFilingRAG:
    """RAG system for SEC filing follow-up questions with smart financial chunking"""

    # SEC section patterns for metadata tagging
    SEC_SECTIONS = {
        r'ITEM\s*1[.\s]': 'business',
        r'ITEM\s*1A[.\s]': 'risk_factors',
        r'ITEM\s*1B[.\s]': 'unresolved_staff_comments',
        r'ITEM\s*2[.\s]': 'properties',
        r'ITEM\s*3[.\s]': 'legal_proceedings',
        r'ITEM\s*4[.\s]': 'mine_safety',
        r'ITEM\s*5[.\s]': 'market_info',
        r'ITEM\s*6[.\s]': 'selected_financial_data',
        r'ITEM\s*7[.\s]': 'md_and_a',
        r'ITEM\s*7A[.\s]': 'market_risk',
        r'ITEM\s*8[.\s]': 'financial_statements',
        r'ITEM\s*9[.\s]': 'changes_disagreements',
        r'ITEM\s*9A[.\s]': 'controls_procedures',
        r'ITEM\s*10[.\s]': 'directors_officers',
        r'ITEM\s*11[.\s]': 'executive_compensation',
        r'ITEM\s*12[.\s]': 'security_ownership',
        r'ITEM\s*13[.\s]': 'related_transactions',
        r'ITEM\s*14[.\s]': 'principal_accountant',
        r'ITEM\s*15[.\s]': 'exhibits',
    }

    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Fast model with high rate limits
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.index_name = "sec-filings"
        self._ensure_index()

    def _ensure_index(self):
        """Ensure Pinecone index exists"""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        self.index = self.pc.Index(self.index_name)

    def _smart_chunk_filing(self, filing_text: str, chunk_size: int = 1500,
                             chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Smart chunking that preserves tables and section context.

        Returns list of dicts with 'text' and 'section' keys.
        """
        chunks = []
        current_section = 'unknown'

        # Split by double newlines to get paragraphs/blocks
        blocks = re.split(r'\n\n+', filing_text)

        current_chunk = ""
        current_chunk_section = current_section

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Check if this block starts a new SEC section
            for pattern, section_name in self.SEC_SECTIONS.items():
                if re.search(pattern, block.upper()):
                    current_section = section_name
                    break

            # Check if this block is a table (starts with |)
            is_table = block.startswith('|') and '|' in block[1:]

            # If it's a table, try to keep it intact
            if is_table:
                # If current chunk + table is too big, save current chunk first
                if current_chunk and len(current_chunk) + len(block) > chunk_size:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': current_chunk_section,
                        'has_table': False
                    })
                    current_chunk = ""

                # If table itself is small enough, add to chunk
                if len(block) <= chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + block
                    else:
                        current_chunk = block
                        current_chunk_section = current_section

                    # Mark this chunk as having a table and save it
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': current_chunk_section,
                        'has_table': True
                    })
                    current_chunk = ""
                else:
                    # Table is too big - save it as its own chunk(s)
                    # Split by rows but keep header
                    table_lines = block.split('\n')
                    header = '\n'.join(table_lines[:2])  # Header + separator

                    table_chunk = header
                    for line in table_lines[2:]:
                        if len(table_chunk) + len(line) > chunk_size:
                            chunks.append({
                                'text': table_chunk.strip(),
                                'section': current_section,
                                'has_table': True
                            })
                            table_chunk = header + '\n' + line
                        else:
                            table_chunk += '\n' + line

                    if table_chunk and table_chunk != header:
                        chunks.append({
                            'text': table_chunk.strip(),
                            'section': current_section,
                            'has_table': True
                        })
            else:
                # Regular text block
                if len(current_chunk) + len(block) > chunk_size:
                    # Save current chunk
                    if current_chunk:
                        chunks.append({
                            'text': current_chunk.strip(),
                            'section': current_chunk_section,
                            'has_table': False
                        })
                    current_chunk = block
                    current_chunk_section = current_section
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + block
                    else:
                        current_chunk = block
                        current_chunk_section = current_section

        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'section': current_chunk_section,
                'has_table': '|' in current_chunk
            })

        return chunks

    def _detect_content_type(self, text: str) -> str:
        """Detect if chunk contains financial data, risk factors, etc."""
        text_lower = text.lower()

        # Check for financial numbers
        has_dollars = bool(re.search(r'\$[\d,]+', text))
        has_percentages = bool(re.search(r'\d+\.?\d*\s*%', text))
        has_table = '|' in text and text.count('|') > 3

        if has_table and (has_dollars or has_percentages):
            return 'financial_table'
        elif has_dollars or 'revenue' in text_lower or 'income' in text_lower:
            return 'financial_data'
        elif 'risk' in text_lower:
            return 'risk_factor'
        else:
            return 'general'

    def index_filing(self, filing_text: str, ticker: str, filing_type: str,
                     filing_date: str) -> Dict[str, Any]:
        """
        Index a filing's text into Pinecone using smart chunking.

        Preserves:
        - Financial tables intact
        - SEC section context as metadata
        - Content type classification

        Args:
            filing_text: The full text of the filing
            ticker: Stock ticker
            filing_type: 10-K or 10-Q
            filing_date: Filing date

        Returns:
            Dict with indexing results
        """
        try:
            # Use smart chunking
            chunks = self._smart_chunk_filing(filing_text)

            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks generated from filing",
                    "ticker": ticker
                }

            # Create embeddings for all chunks
            vectors = []
            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data['text']

                # Skip empty chunks
                if not chunk_text or len(chunk_text) < 10:
                    continue

                # Create embedding
                embedding = self.embeddings.embed_query(chunk_text)

                # Detect content type
                content_type = self._detect_content_type(chunk_text)

                # Create vector with rich metadata
                vector_id = f"{ticker}_{filing_type}_{filing_date}_{i}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "ticker": ticker,
                        "filing_type": filing_type,
                        "filing_date": filing_date,
                        "chunk_index": i,
                        "section": chunk_data['section'],
                        "has_table": chunk_data['has_table'],
                        "content_type": content_type,
                        "text": chunk_text[:2000]  # Store more text in metadata
                    }
                })

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=ticker)

            # Count chunks by section for reporting
            sections_indexed = {}
            for chunk_data in chunks:
                section = chunk_data['section']
                sections_indexed[section] = sections_indexed.get(section, 0) + 1

            return {
                "success": True,
                "ticker": ticker,
                "chunks_indexed": len(vectors),
                "filing_type": filing_type,
                "sections_indexed": sections_indexed,
                "tables_preserved": sum(1 for c in chunks if c['has_table'])
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ticker": ticker
            }

    def query(self, question: str, ticker: str, top_k: int = 5,
              section_filter: Optional[str] = None,
              content_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the indexed filing to answer a follow-up question.

        Args:
            question: User's question
            ticker: Stock ticker to search in
            top_k: Number of relevant chunks to retrieve
            section_filter: Optional SEC section to filter by (e.g., 'risk_factors', 'financial_statements')
            content_type_filter: Optional content type filter ('financial_table', 'financial_data', 'risk_factor')

        Returns:
            Dict with answer and sources
        """
        try:
            # Create embedding for the question
            question_embedding = self.embeddings.embed_query(question)

            # Build filter if specified
            filter_dict = {}
            if section_filter:
                filter_dict["section"] = {"$eq": section_filter}
            if content_type_filter:
                filter_dict["content_type"] = {"$eq": content_type_filter}

            # Query Pinecone
            query_params = {
                "vector": question_embedding,
                "top_k": top_k,
                "include_metadata": True,
                "namespace": ticker
            }
            if filter_dict:
                query_params["filter"] = filter_dict

            results = self.index.query(**query_params)

            if not results.matches:
                return {
                    "success": False,
                    "error": f"No indexed data found for {ticker}",
                    "answer": None
                }

            # Extract relevant chunks with rich metadata
            context_chunks = []
            sources = []
            for match in results.matches:
                chunk_text = match.metadata.get("text", "")
                section = match.metadata.get("section", "unknown")
                has_table = match.metadata.get("has_table", False)

                # Format context with section info
                section_label = section.replace('_', ' ').title()
                formatted_chunk = f"[{section_label}]\n{chunk_text}"
                context_chunks.append(formatted_chunk)

                sources.append({
                    "filing_type": match.metadata.get("filing_type"),
                    "filing_date": match.metadata.get("filing_date"),
                    "section": section,
                    "has_table": has_table,
                    "content_type": match.metadata.get("content_type"),
                    "chunk_index": match.metadata.get("chunk_index"),
                    "score": match.score
                })

            # Build context
            context = "\n\n---\n\n".join(context_chunks)

            # Generate answer using LLM
            prompt = f"""You are an expert financial analyst. Answer the following question
based ONLY on the provided context from {ticker}'s SEC filing.

IMPORTANT INSTRUCTIONS:
1. If the context contains financial tables with numbers, extract the EXACT numbers.
2. Always include specific dollar amounts, percentages, and dates when available.
3. If the answer cannot be found in the context, say "I cannot find this information in the filing."
4. Cite the SEC section where you found the information (e.g., "From Item 7 - MD&A").

Context from SEC Filing:
{context}

Question: {question}

Provide a clear answer with SPECIFIC NUMBERS and citations:"""

            response = self.llm.invoke(prompt)
            answer = response.content

            return {
                "success": True,
                "question": question,
                "answer": answer,
                "ticker": ticker,
                "sources": sources,
                "context_used": len(context_chunks),
                "sections_searched": list(set(s["section"] for s in sources))
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }

    def query_financial_metric(self, metric_name: str, ticker: str) -> Dict[str, Any]:
        """
        Query specifically for a financial metric.

        This is optimized for extracting specific numbers like revenue, net income, etc.

        Args:
            metric_name: Name of the metric (e.g., 'total revenue', 'net income', 'operating margin')
            ticker: Stock ticker

        Returns:
            Dict with the extracted metric value and context
        """
        # Map common metrics to optimal search strategies
        metric_queries = {
            'revenue': f"What is {ticker}'s total revenue or net sales for the fiscal year?",
            'net_income': f"What is {ticker}'s net income for the fiscal year?",
            'gross_profit': f"What is {ticker}'s gross profit and gross margin?",
            'operating_income': f"What is {ticker}'s operating income and operating margin?",
            'total_assets': f"What are {ticker}'s total assets?",
            'total_debt': f"What is {ticker}'s total debt (long-term and short-term)?",
            'cash': f"What is {ticker}'s cash and cash equivalents?",
            'free_cash_flow': f"What is {ticker}'s free cash flow?",
            'eps': f"What is {ticker}'s earnings per share (EPS)?",
            'roe': f"What is {ticker}'s return on equity (ROE)?",
        }

        # Use specific query if available, otherwise use the metric name directly
        question = metric_queries.get(metric_name.lower(), f"What is {ticker}'s {metric_name}?")

        # Query with preference for financial tables
        result = self.query(
            question=question,
            ticker=ticker,
            top_k=8,  # Get more chunks for financial queries
            content_type_filter='financial_table'  # Prefer tables
        )

        # If no results from tables, try without filter
        if not result.get('success') or 'cannot find' in result.get('answer', '').lower():
            result = self.query(
                question=question,
                ticker=ticker,
                top_k=8
            )

        return result

    def delete_filing(self, ticker: str) -> Dict[str, Any]:
        """Delete all vectors for a specific ticker"""
        try:
            self.index.delete(delete_all=True, namespace=ticker)
            return {
                "success": True,
                "ticker": ticker,
                "message": f"Deleted all vectors for {ticker}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_suggested_questions(self, ticker: str) -> List[str]:
        """Get suggested follow-up questions for a filing"""
        return [
            f"What are {ticker}'s main revenue streams?",
            f"What are the biggest risk factors for {ticker}?",
            f"How has {ticker}'s revenue changed year-over-year?",
            f"What is {ticker}'s competitive advantage?",
            f"What are {ticker}'s key growth initiatives?",
            f"How much debt does {ticker} have?",
            f"What are the main segments of {ticker}'s business?"
        ]


# Test function
if __name__ == "__main__":
    print("Testing Pinecone RAG...")

    rag = SECFilingRAG()

    # Test with sample text
    sample_text = """
    Apple Inc. designs, manufactures, and markets smartphones, personal computers,
    tablets, wearables, and accessories worldwide. The company offers iPhone, Mac,
    iPad, Apple Watch, and AirPods. Apple's services include App Store, Apple Music,
    Apple TV+, and iCloud. Revenue for fiscal 2025 was $391 billion, an increase
    of 4% from the prior year. The iPhone segment contributed $201 billion, while
    Services generated $96 billion. Risk factors include global economic conditions,
    supply chain disruptions, and intense competition in the technology sector.
    """

    # Index sample
    result = rag.index_filing(
        filing_text=sample_text,
        ticker="AAPL_TEST",
        filing_type="10-K",
        filing_date="2025-10-31"
    )
    print(f"Indexing result: {result}")

    # Query
    query_result = rag.query(
        question="What is Apple's revenue?",
        ticker="AAPL_TEST"
    )
    print(f"\nQuery result:")
    print(f"Answer: {query_result.get('answer', 'N/A')}")

    # Cleanup test data
    rag.delete_filing("AAPL_TEST")
    print("\nTest data cleaned up")

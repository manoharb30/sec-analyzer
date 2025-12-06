"""
SEC Filing Downloader Tool
Downloads SEC filings from EDGAR as PDF and extracts text content
PDFs preserve financial tables and numbers better than HTML
"""

import os
import re
import requests
import tempfile
from typing import Optional, Type, Dict, List, ClassVar
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pdfplumber


class SECDownloaderInput(BaseModel):
    """Input schema for SEC Filing Downloader"""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, MSFT)")
    filing_type: str = Field(default="10-K", description="Filing type: 10-K or 10-Q")


class SECDownloaderTool(BaseTool):
    """Tool to download and extract text from SEC filings (PDF version)"""

    name: str = "SEC Filing Downloader"
    description: str = (
        "Download an SEC filing for a given ticker and extract text content. "
        "Gets the latest 10-K (annual) or 10-Q (quarterly) filing as PDF."
    )
    args_schema: Type[BaseModel] = SECDownloaderInput

    # Headers for SEC API
    HEADERS: ClassVar[Dict[str, str]] = {
        'User-Agent': 'SEC-Analyzer Research contact@example.com',
        'Accept': 'application/json,application/pdf,text/html',
    }

    def _run(self, ticker: str, filing_type: str = "10-K") -> Dict:
        """
        Download SEC filing as PDF and extract text

        Args:
            ticker: Stock ticker symbol
            filing_type: 10-K or 10-Q

        Returns:
            dict with extracted text and metadata
        """
        try:
            # Step 1: Get CIK from ticker
            cik = self._get_cik(ticker)
            if not cik:
                return {
                    "success": False,
                    "error": f"Could not find CIK for ticker {ticker}",
                    "ticker": ticker
                }

            # Step 2: Get filing metadata and find PDF URL
            filing_info = self._get_filing_info(cik, filing_type)
            if not filing_info:
                return {
                    "success": False,
                    "error": f"Could not find {filing_type} filing for {ticker}",
                    "ticker": ticker
                }

            # Step 3: Try to download PDF first, fallback to HTML
            pdf_url = filing_info.get('pdf_url')
            text = None

            if pdf_url:
                print(f"Downloading PDF from: {pdf_url}")
                text = self._download_and_extract_pdf(pdf_url)

            # Fallback to HTML if PDF fails
            if not text:
                print(f"PDF not available, falling back to HTML")
                html_url = filing_info.get('url')
                html_content = self._download_filing(html_url)
                if html_content:
                    text = self._extract_text_from_html(html_content)

            if not text:
                return {
                    "success": False,
                    "error": "Failed to extract text from filing",
                    "ticker": ticker
                }

            return {
                "success": True,
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "filing_date": filing_info.get('filing_date'),
                "filing_url": pdf_url or filing_info.get('url'),
                "company_name": filing_info.get('company_name'),
                "full_text": text,
                "full_text_length": len(text),
                "truncated": False
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ticker": ticker
            }

    def _get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK number from ticker symbol"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()

            data = response.json()
            ticker_upper = ticker.upper()

            for entry in data.values():
                if entry.get('ticker') == ticker_upper:
                    cik = str(entry.get('cik_str'))
                    return cik.zfill(10)

            return None
        except Exception as e:
            print(f"Error getting CIK: {e}")
            return None

    def _get_filing_info(self, cik: str, filing_type: str) -> Optional[Dict]:
        """Get filing metadata from SEC data API, including PDF URL"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()

            data = response.json()
            company_name = data.get('name', '')

            filings = data.get('filings', {}).get('recent', {})
            forms = filings.get('form', [])
            accession_numbers = filings.get('accessionNumber', [])
            filing_dates = filings.get('filingDate', [])
            primary_documents = filings.get('primaryDocument', [])

            # Find the latest filing of requested type
            for i, form in enumerate(forms):
                if form == filing_type:
                    accession = accession_numbers[i].replace('-', '')
                    accession_dashed = accession_numbers[i]
                    primary_doc = primary_documents[i]
                    cik_clean = cik.lstrip('0')

                    # Build URLs
                    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession}"
                    html_url = f"{base_url}/{primary_doc}"

                    # Try to find PDF in the filing directory
                    pdf_url = self._find_pdf_url(base_url, cik_clean, accession)

                    return {
                        'url': html_url,
                        'pdf_url': pdf_url,
                        'filing_date': filing_dates[i],
                        'accession_number': accession_dashed,
                        'company_name': company_name,
                        'primary_document': primary_doc,
                        'base_url': base_url
                    }

            return None
        except Exception as e:
            print(f"Error getting filing info: {e}")
            return None

    def _find_pdf_url(self, base_url: str, cik: str, accession: str) -> Optional[str]:
        """Try to find PDF version of the filing"""
        try:
            # SEC provides a standard PDF link format
            # Try the filing index to find PDF
            index_url = f"{base_url}/index.json"
            response = requests.get(index_url, headers=self.HEADERS, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get('directory', {}).get('item', [])

                for item in items:
                    name = item.get('name', '').lower()
                    # Look for PDF files (usually the main filing)
                    if name.endswith('.pdf') and ('10-k' in name or '10k' in name or '10-q' in name or '10q' in name):
                        return f"{base_url}/{item.get('name')}"

                # If no specific 10-K PDF, look for any PDF
                for item in items:
                    name = item.get('name', '').lower()
                    if name.endswith('.pdf') and 'ex' not in name:  # Exclude exhibits
                        return f"{base_url}/{item.get('name')}"

            return None
        except Exception as e:
            print(f"Error finding PDF: {e}")
            return None

    def _download_and_extract_pdf(self, url: str) -> Optional[str]:
        """Download PDF and extract text using pdfplumber"""
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=120)
            response.raise_for_status()

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            # Extract text from PDF
            text_parts = []
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    # Also extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            for row in table:
                                if row:
                                    row_text = ' | '.join([str(cell) if cell else '' for cell in row])
                                    text_parts.append(row_text)

            # Clean up temp file
            os.unlink(tmp_path)

            text = '\n'.join(text_parts)

            # Clean up text
            text = self._clean_text(text)

            return text if text else None

        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return None

    def _download_filing(self, url: str) -> Optional[str]:
        """Download HTML filing from SEC EDGAR"""
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=60)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error downloading filing: {e}")
            return None

    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Extract text from HTML filing with proper table preservation.
        Tables are converted to markdown format to preserve financial data structure.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'meta', 'link', 'head', 'noscript']):
            element.decompose()

        # Remove hidden elements
        for element in soup.find_all(style=re.compile(r'display:\s*none', re.IGNORECASE)):
            element.decompose()

        # Process tables FIRST - convert to markdown format
        tables_extracted = []
        for table in soup.find_all('table'):
            markdown_table = self._table_to_markdown(table)
            if markdown_table:
                tables_extracted.append(markdown_table)
                # Replace table with a placeholder that includes the markdown
                placeholder = soup.new_tag('div')
                placeholder.string = f"\n\n{markdown_table}\n\n"
                table.replace_with(placeholder)

        # Now extract text with structure preserved
        text_parts = []

        # Process the document maintaining structure
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'span', 'li']):
            text = element.get_text(strip=True)
            if text and len(text) > 1:
                # Identify SEC section headers
                if self._is_sec_section_header(text):
                    text_parts.append(f"\n\n## {text}\n")
                else:
                    text_parts.append(text)

        # If structured extraction didn't work well, fall back to full text
        if len(text_parts) < 100:
            text = soup.get_text(separator='\n', strip=True)
        else:
            text = '\n'.join(text_parts)

        return self._clean_text(text)

    def _table_to_markdown(self, table) -> Optional[str]:
        """
        Convert HTML table to markdown format, preserving financial data.
        Returns None if table is empty or invalid.
        """
        rows = []

        # Extract all rows (including header rows)
        for tr in table.find_all('tr'):
            cells = []
            for cell in tr.find_all(['th', 'td']):
                # Get cell text, preserving numbers
                cell_text = cell.get_text(strip=True)
                # Clean up but preserve financial formatting
                cell_text = re.sub(r'\s+', ' ', cell_text)
                # Handle empty cells
                if not cell_text:
                    cell_text = '-'
                cells.append(cell_text)

            if cells and any(c != '-' for c in cells):  # Skip completely empty rows
                rows.append(cells)

        if not rows or len(rows) < 2:
            return None

        # Normalize column count
        max_cols = max(len(row) for row in rows)
        for row in rows:
            while len(row) < max_cols:
                row.append('-')

        # Build markdown table
        markdown_lines = []

        # Header row
        markdown_lines.append('| ' + ' | '.join(rows[0]) + ' |')

        # Separator row
        markdown_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')

        # Data rows
        for row in rows[1:]:
            markdown_lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(markdown_lines)

    def _is_sec_section_header(self, text: str) -> bool:
        """Check if text is an SEC filing section header (Item 1, Item 1A, etc.)"""
        sec_headers = [
            r'^ITEM\s+\d+[A-Z]?\b',
            r'^PART\s+[IVX]+\b',
            r'^SIGNATURES?\b',
            r'^EXHIBIT\s+INDEX\b',
            r'^FINANCIAL\s+STATEMENTS\b',
            r'^MANAGEMENT.S\s+DISCUSSION\b',
            r'^RISK\s+FACTORS\b',
            r'^BUSINESS\b',
            r'^PROPERTIES\b',
            r'^LEGAL\s+PROCEEDINGS\b',
        ]
        text_upper = text.upper().strip()
        return any(re.match(pattern, text_upper) for pattern in sec_headers)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'_{3,}', '', text)

        # Remove common artifacts
        text = re.sub(r'http://[^\s]+', '', text)
        text = re.sub(r'https://[^\s]+', '', text)

        return text.strip()


# Test function
if __name__ == "__main__":
    tool = SECDownloaderTool()

    print("Testing SEC Downloader with AAPL (PDF)...")
    result = tool._run("AAPL", "10-K")

    print(f"\nSuccess: {result.get('success')}")
    print(f"Company: {result.get('company_name')}")
    print(f"Filing Date: {result.get('filing_date')}")
    print(f"Filing URL: {result.get('filing_url')}")
    print(f"Full text length: {result.get('full_text_length', 0)} chars")

    if result.get('full_text'):
        text = result['full_text']
        print(f"\nFirst 2000 chars of filing:")
        print(text[:2000])

        # Check for financial numbers
        import re
        numbers = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?', text)
        print(f"\nSample financial numbers found: {numbers[:10]}")

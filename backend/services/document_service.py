"""Document parsing service.

This deployment is optimized for Vercel serverless size limits.
Only PDF parsing is supported.
"""

from io import BytesIO
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def parse_document_bytes(
    data: bytes,
    mimetype: str,
    filename: Optional[str] = None,
) -> dict:
    """
    Parse document content from various formats.
    
    Returns:
    {
        "filename": str,
        "mimetype": str,
        "content": str,  # Extracted text content
        "metadata": dict,  # Additional metadata like page count, sheets, etc.
    }
    """
    filename = filename or "document"
    content = ""
    metadata = {}
    
    # Determine document type
    mime_lower = (mimetype or "").lower()
    fname_lower = filename.lower()
    
    try:
        # PDF parsing (only supported format)
        if "pdf" in mime_lower or fname_lower.endswith(".pdf"):
            if PdfReader is None:
                raise RuntimeError("pypdf not installed. Run: pip install pypdf")
            
            pdf = PdfReader(BytesIO(data))
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[Page {i+1}]\n{text.strip()}")
            
            content = "\n\n".join(pages)
            metadata = {
                "page_count": len(pdf.pages),
                "format": "PDF"
            }

        else:
            raise ValueError("Unsupported document type. Only PDF is supported.")
        
        # Truncate if too large (limit to ~100k chars)
        if len(content) > 100_000:
            content = content[:100_000] + "\n\n[Content truncated due to size...]"
            metadata["truncated"] = True
        
        return {
            "filename": filename,
            "mimetype": mimetype,
            "content": content,
            "metadata": metadata,
        }
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse document: {str(e)}")

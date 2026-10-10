import os
import fitz  # PyMuPDF
from docx import Document
from typing import Dict, Any, List

def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract page-indexed text from PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    pages: List[Dict[str, Any]] = []
    full_text_chunks: List[str] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        page_num = page_idx + 1
        pages.append({
            "page_number": page_num,
            "text": text,
        })
        if text:
            full_text_chunks.append(f"--- Page {page_num} ---\n{text}")

    doc.close()
    return {
        "full_text": "\n\n".join(full_text_chunks),
        "pages": pages,
        "page_count": len(pages),
    }

def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
    """Extract paragraph and section text from DOCX using python-docx."""
    doc = Document(file_path)
    paragraphs: List[str] = []
    for p in doc.paragraphs:
        if p.text.strip():
            paragraphs.append(p.text.strip())

    full_text = "\n\n".join(paragraphs)
    return {
        "full_text": full_text,
        "pages": [{"page_number": 1, "text": full_text}],
        "page_count": 1,
    }

def extract_text_from_file(file_path: str, filename: str) -> Dict[str, Any]:
    """Extract text from PDF, DOCX, or plain text document."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        # Fallback to plain text
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "full_text": content,
            "pages": [{"page_number": 1, "text": content}],
            "page_count": 1,
        }

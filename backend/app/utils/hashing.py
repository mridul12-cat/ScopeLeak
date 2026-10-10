import hashlib

def compute_text_hash(text: str) -> str:
    """Compute sha256 hash of normalized text."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def compute_file_hash(content_bytes: bytes) -> str:
    """Compute sha256 hash of file bytes."""
    return hashlib.sha256(content_bytes).hexdigest()

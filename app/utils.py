import os
import re
from typing import List

def list_text_files(root: str, exts=None):
    if exts is None:
        exts = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.rst'}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            _, e = os.path.splitext(fn)
            if e.lower() in exts:
                yield os.path.join(dirpath, fn)

def read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks
from pathlib import Path
import json

KB_FILE = Path("kb/chunks_sample.jsonl")

def load_chunks():
    if not KB_FILE.exists():
        return []
    return [json.loads(line) for line in KB_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

def retrieve(query: str, k: int = 3):
    q = (query or "").lower().split()
    scored = []
    for chunk in load_chunks():
        text = (chunk.get("text") or "").lower()
        score = sum(1 for w in q if w in text)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]

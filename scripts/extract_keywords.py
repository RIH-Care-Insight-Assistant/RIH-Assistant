#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys, math, collections
from pathlib import Path

STOP = set("""
the a an and or of to for in on at by with from is are was were be being been
it this that these those you your we our us they their i
campus service services page hours location contact
""".split())

WORD_RE = re.compile(r"[a-z0-9]+")

def tokens(s: str):
    return [w for w in WORD_RE.findall(s.lower()) if w not in STOP and len(w) > 2]

def top_terms(pages, k=50):
    df = collections.Counter()
    per_doc = []
    for p in pages:
        t = set(tokens(p["text"]))
        per_doc.append(t)
        for w in t: df[w] += 1
    N = len(pages)
    idf = {w: math.log((N - d + 0.5)/(d + 0.5) + 1.0) for w, d in df.items()}

    # global tf counts
    tf = collections.Counter()
    for p in pages:
        tf.update(tokens(p["text"]))

    # rank by tf*idf
    scores = [(w, tf[w] * idf.get(w, 0.0)) for w in tf]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:k]

def bigrams(words):
    return list(zip(words, words[1:]))

def top_bigrams(pages, k=50):
    bg = collections.Counter()
    for p in pages:
        ws = tokens(p["text"])
        bg.update([" ".join(b) for b in bigrams(ws)])
    return bg.most_common(k)

def main():
    inp = Path("data/public_crawl/pages.jsonl")
    if not inp.exists():
        print("Run scripts/crawl_site.py first", file=sys.stderr)
        sys.exit(1)
    pages = [json.loads(l) for l in inp.read_text(encoding="utf-8").splitlines() if l.strip()]
    uni = top_terms(pages, k=80)
    bi = top_bigrams(pages, k=80)

    Path("data/public_crawl").mkdir(parents=True, exist_ok=True)
    with open("data/public_crawl/candidates.csv", "w", encoding="utf-8") as f:
        f.write("kind,term,score_or_freq\n")
        for w, s in uni:
            f.write(f"unigram,{w},{round(s,3)}\n")
        for w, s in bi:
            f.write(f"bigram,{w},{s}\n")
    print("Wrote data/public_crawl/candidates.csv")

if __name__ == "__main__":
    main()

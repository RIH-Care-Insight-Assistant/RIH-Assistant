#!/usr/bin/env python3
from __future__ import annotations
import time, re, json, sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

SEED_URLS = [
    "https://health.umbc.edu/",
    # add your Title IX root here:
    # "https://oei.umbc.edu/title-ix/",
]
ALLOWED_NETLOCS = {urlparse(u).netloc for u in SEED_URLS}
MAX_PAGES = 200
SLEEP_SEC = 0.5

def is_allowed(url: str) -> bool:
    u = urlparse(url)
    if u.scheme not in {"http", "https"}: return False
    if u.netloc not in ALLOWED_NETLOCS: return False
    return True

def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # remove navs/footers/menus as best-effort
    for sel in ["nav", "footer", ".menu", ".site-header", ".site-footer", ".breadcrumbs"]:
        for tag in soup.select(sel):
            tag.decompose()
    # kill scripts/styles
    for t in soup(["script","style","noscript"]): t.extract()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def crawl(seed_urls):
    seen, queue, out = set(), list(seed_urls), []
    ses = requests.Session()
    while queue and len(out) < MAX_PAGES:
        url = queue.pop(0)
        if url in seen or not is_allowed(url): continue
        seen.add(url)
        try:
            r = ses.get(url, timeout=15)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""): continue
            text = clean_text(r.text)
            title = re.search(r"<title>(.*?)</title>", r.text, re.I|re.S)
            title = (title.group(1).strip() if title else url)
            out.append({"url": url, "title": title, "text": text})
            # enqueue links
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                nxt = urljoin(url, a["href"])
                if is_allowed(nxt) and nxt not in seen:
                    queue.append(nxt)
            time.sleep(SLEEP_SEC)
        except requests.RequestException:
            continue
    return out

def main():
    pages = crawl(SEED_URLS)
    with open("data/public_crawl/pages.jsonl", "w", encoding="utf-8") as f:
        for p in pages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"Wrote {len(pages)} pages to data/public_crawl/pages.jsonl")

if __name__ == "__main__":
    sys.exit(main())

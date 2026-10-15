"""Secure source ingestion: fetch an approved public page into staging as `pending`.

SSRF defenses: HTTPS only; no credentials or non-default ports; host must be on the RAG
policy allowlist; every resolved address must be public (no private, loopback,
link-local, multicast, reserved or unspecified ranges); redirects are followed manually
and each hop is re-validated; the connection is pinned to the validated address set
by checking the peer address after connecting; size, content type and total time are
bounded. Fetched text is scanned for instruction-like content. Nothing ingested is
citable until an authorized reviewer approves it.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit

import httpx

from .governance import RagPolicy
from .injection import injection_signals

MAX_BYTES = 1_000_000
MAX_REDIRECTS = 3
TOTAL_TIMEOUT_S = 10.0
ALLOWED_TYPES = ("text/html", "text/plain")

Resolver = Callable[[str, int], List[str]]


class IngestRejected(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class IngestResult:
    record: dict
    signals: List[str]
    final_url: str


def system_resolver(host: str, port: int) -> List[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return sorted({i[4][0] for i in infos})


def _public(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr.split("%")[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    blocked = (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved
               or ip.is_unspecified)
    return ip.is_global and not blocked


def validate_url(url: str, policy: RagPolicy, resolver: Resolver) -> Tuple[str, List[str]]:
    """Return (host, validated addresses) or raise IngestRejected."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise IngestRejected("malformed_url") from None
    if parts.scheme != "https":
        raise IngestRejected("https_required")
    if parts.username or parts.password:
        raise IngestRejected("credentials_in_url")
    if port not in (None, 443):
        raise IngestRejected("port_not_allowed")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or not policy.host_allowed(f"https://{host}/"):
        raise IngestRejected("host_not_allowed")
    try:
        ipaddress.ip_address(host)
        raise IngestRejected("ip_literal_not_allowed")
    except ValueError:
        pass
    try:
        addrs = resolver(host, 443)
    except OSError:
        raise IngestRejected("dns_failure") from None
    if not addrs or not all(_public(a) for a in addrs):
        raise IngestRejected("non_public_address")
    return host, addrs


def _extract(html: str, content_type: str) -> Tuple[str, str]:
    if content_type.startswith("text/plain"):
        lines = [ln.strip() for ln in html.splitlines() if ln.strip()]
        return (lines[0][:120] if lines else "Untitled"), " ".join(lines)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "template", "svg", "nav", "footer", "header", "form"]):
        tag.decompose()
    title = (soup.title.get_text(" ", strip=True) if soup.title else "") or "Untitled"
    main = soup.find("main") or soup.body or soup
    text = " ".join(main.get_text(" ", strip=True).split())
    return title[:200], text


def fetch_source(
    url: str,
    policy: RagPolicy,
    *,
    category: str = "ingested",
    resolver: Resolver = system_resolver,
    transport: Optional[httpx.BaseTransport] = None,
    today: Optional[date] = None,
) -> IngestResult:
    deadline = time.monotonic() + TOTAL_TIMEOUT_S
    current = url
    with httpx.Client(transport=transport, follow_redirects=False, timeout=5.0, trust_env=False,
                      headers={"User-Agent": "RIH-Care-Insight-Prototype/1.0 (student project; synthetic demo)"}) as client:
        for _hop in range(MAX_REDIRECTS + 1):
            if time.monotonic() > deadline:
                raise IngestRejected("timeout")
            _host, addrs = validate_url(current, policy, resolver)
            try:
                with client.stream("GET", current) as resp:
                    peer = _peer_address(resp)
                    if peer is not None and peer not in addrs:
                        raise IngestRejected("address_changed")  # DNS rebinding between check and connect
                    if resp.status_code in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("location")
                        if not loc:
                            raise IngestRejected("bad_redirect")
                        current = urljoin(current, loc)
                        continue
                    if resp.status_code != 200:
                        raise IngestRejected(f"http_{resp.status_code}")
                    ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                    if ctype not in ALLOWED_TYPES:
                        raise IngestRejected("content_type_not_allowed")
                    declared = resp.headers.get("content-length")
                    if declared and declared.isdigit() and int(declared) > MAX_BYTES:
                        raise IngestRejected("too_large")
                    body = bytearray()
                    for chunk in resp.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise IngestRejected("too_large")
                        if time.monotonic() > deadline:
                            raise IngestRejected("timeout")
                    text = body.decode(resp.encoding or "utf-8", errors="replace")
            except httpx.HTTPError:
                raise IngestRejected("fetch_failed") from None
            title, content = _extract(text, ctype)
            if len(content) < 40:
                raise IngestRejected("too_little_text")
            record = {
                "title": title, "url": current, "category": category[:40], "page_type": "general",
                "updated_on": (today or date.today()).isoformat(), "text": content[:4000],
            }
            return IngestResult(record, injection_signals(f"{title}\n{content}"), current)
    raise IngestRejected("too_many_redirects")


def _peer_address(resp: httpx.Response) -> Optional[str]:
    stream = resp.extensions.get("network_stream")
    if stream is None:
        return None  # test transports have no socket
    try:
        info = stream.get_extra_info("server_addr")
        return info[0] if info else None
    except Exception:
        return None

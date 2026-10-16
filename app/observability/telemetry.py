"""Privacy-safe observability: OpenTelemetry traces and metrics, structured JSON logs.

Rules (contract C4-local-v1 §5):
- No message text, tool arguments, query strings, cookies, usernames or IP addresses in
  spans, metrics or logs. Exporters keep only allowlisted span attributes.
- Routes are recorded as templates (`/api/v1/sessions/{session_id}`), never raw paths.
- Each app instance owns its providers (no global state), so tests and multiple apps in one
  process stay isolated. Exporters are local only: an in-memory ring buffer (shown to staff)
  and, optionally, a JSONL file (`RIH_TRACE_FILE`).
"""

from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections import Counter, deque
from typing import Any, Deque, Dict, Iterable, List, Optional, Sequence

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode

SERVICE_NAME = "rih-api"

# Only these span attributes ever leave the process.
ALLOWED_ATTRIBUTES = frozenset({
    "http.method", "http.route", "http.status_code", "rih.request_id", "rih.error_class",
    "rih.response_type", "rih.safety_lane", "rih.persisted", "rih.tool", "rih.tool_status", "rih.rule_id",
    "rih.planner", "rih.planner_status", "rih.retrieval_status", "rih.hits", "rih.incident", "rih.channel",
})

LATENCY_BUCKETS_MS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)


def classify_status(status: int) -> str:
    if status == 429:
        return "rate_limited"
    if status in (401, 403):
        return "auth_denied"
    if status == 503:
        return "dependency_unavailable"
    if status >= 500:
        return "internal_error"
    if status >= 400:
        return "client_error"
    return "ok"


class RingBufferExporter(SpanExporter):
    """Keeps the most recent finished spans (already filtered) for the staff observability view."""

    def __init__(self, capacity: int = 500):
        self.spans: Deque[Dict[str, Any]] = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self._lock:
            for s in spans:
                self.spans.append(span_record(s))
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.spans)[-limit:][::-1]


class JsonlFileExporter(SpanExporter):
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            with self._lock, open(self.path, "a", encoding="utf-8") as f:
                for s in spans:
                    f.write(json.dumps(span_record(s)) + "\n")
            return SpanExportResult.SUCCESS
        except OSError:
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        pass


def span_record(s: ReadableSpan) -> Dict[str, Any]:
    ctx = s.get_span_context()
    return {
        "name": s.name,
        "trace_id": format(ctx.trace_id, "032x"),
        "span_id": format(ctx.span_id, "016x"),
        "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
        "duration_ms": round(((s.end_time or 0) - (s.start_time or 0)) / 1e6, 3),
        "status": s.status.status_code.name,
        "attributes": {k: v for k, v in (s.attributes or {}).items() if k in ALLOWED_ATTRIBUTES},
    }


class Telemetry:
    def __init__(self, *, trace_file: Optional[str] = None, capacity: int = 500):
        resource = Resource.create({"service.name": SERVICE_NAME})
        self.ring = RingBufferExporter(capacity)
        self.tracer_provider = TracerProvider(resource=resource)
        # Every exporter serialises through span_record(), which keeps only allowlisted attributes.
        self.tracer_provider.add_span_processor(SimpleSpanProcessor(self.ring))
        if trace_file:
            self.tracer_provider.add_span_processor(SimpleSpanProcessor(JsonlFileExporter(trace_file)))
        self.tracer = self.tracer_provider.get_tracer("rih")
        self.reader = InMemoryMetricReader()
        self.meter_provider = MeterProvider(resource=resource, metric_readers=[self.reader])
        meter = self.meter_provider.get_meter("rih")
        self.requests = meter.create_counter("rih.http.requests", description="HTTP requests by route and class")
        self.latency = meter.create_histogram("rih.http.duration", unit="ms", description="HTTP request latency")
        self.tool_calls = meter.create_counter("rih.tool.calls", description="Governed tool calls by tool and status")
        self.chat_turns = meter.create_counter("rih.chat.turns", description="Chat turns by response type and lane")
        self.security_events = meter.create_counter("rih.security.events", description="Denials and abuse signals")
        self.planner = meter.create_counter("rih.planner.outcomes", description="Model planner outcomes")
        self.started = time.time()
        # Exact per-route latency samples (bounded) for p50/p95; histograms keep the OTel view.
        self._samples: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()
        self.log = logging.getLogger("rih.http")
        self.security_log = logging.getLogger("rih.security")

    # ---- recording helpers (all attributes are allowlisted values, never user content)
    def record_request(self, method: str, route: str, status: int, duration_ms: float, request_id: str) -> None:
        cls = classify_status(status)
        self.requests.add(1, {"http.route": route, "http.method": method, "rih.error_class": cls})
        self.latency.record(duration_ms, {"http.route": route})
        with self._lock:
            self._samples.setdefault(route, deque(maxlen=2000)).append(duration_ms)
        self.log.info("http_request", extra={"fields": {
            "method": method, "route": route, "status": status, "duration_ms": round(duration_ms, 2),
            "error_class": cls, "request_id": request_id}})
        if cls in ("auth_denied", "rate_limited"):
            self.security_events.add(1, {"rih.error_class": cls, "http.route": route})
            self.security_log.warning("security_event", extra={"fields": {
                "error_class": cls, "route": route, "status": status, "request_id": request_id}})

    def record_tool(self, tool: str, status: str, rule: str) -> None:
        self.tool_calls.add(1, {"rih.tool": tool, "rih.tool_status": status})
        if status == "denied":
            self.security_events.add(1, {"rih.error_class": "authz_denied", "rih.tool": tool})
            self.security_log.warning("authz_denied", extra={"fields": {"tool": tool, "rule_id": rule, "channel": "agent"}})
        elif status in ("timeout", "error", "invalid_output"):
            self.security_log.warning("tool_failure", extra={"fields": {"tool": tool, "status": status}})

    def record_turn(self, response_type: str, lane: Optional[str], persisted: bool) -> None:
        self.chat_turns.add(1, {"rih.response_type": response_type, "rih.safety_lane": lane or "none",
                                "rih.persisted": persisted})

    def record_planner(self, status: str) -> None:
        self.planner.add(1, {"rih.planner_status": status})

    # ---- reading
    def percentiles(self) -> Dict[str, Dict[str, float]]:
        out = {}
        with self._lock:
            for route, samples in self._samples.items():
                s = sorted(samples)
                if s:  # nearest-rank percentiles over the bounded sample window
                    out[route] = {"count": len(s), "p50_ms": round(s[max(0, math.ceil(0.50 * len(s)) - 1)], 2),
                                  "p95_ms": round(s[max(0, math.ceil(0.95 * len(s)) - 1)], 2),
                                  "max_ms": round(s[-1], 2)}
        return out

    def counters(self) -> Dict[str, List[Dict[str, Any]]]:
        data = self.reader.get_metrics_data()
        out: Dict[str, List[Dict[str, Any]]] = {}
        if data is None:
            return out
        for rm in data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    if m.name == "rih.http.duration":
                        continue
                    out[m.name] = [{"attributes": dict(p.attributes), "value": p.value} for p in m.data.data_points]
        return out

    def summary(self) -> Dict[str, Any]:
        counters = self.counters()

        def total_by(name: str, key: str) -> Dict[str, int]:
            c: Counter = Counter()
            for p in counters.get(name, []):
                c[str(p["attributes"].get(key))] += p["value"]
            return dict(c)

        return {
            "service": SERVICE_NAME,
            "uptime_s": round(time.time() - self.started, 1),
            "requests_by_class": total_by("rih.http.requests", "rih.error_class"),
            "latency_by_route": self.percentiles(),
            "tool_calls_by_status": total_by("rih.tool.calls", "rih.tool_status"),
            "tool_calls_by_tool": total_by("rih.tool.calls", "rih.tool"),
            "chat_turns_by_type": total_by("rih.chat.turns", "rih.response_type"),
            "chat_turns_by_lane": total_by("rih.chat.turns", "rih.safety_lane"),
            "security_events": total_by("rih.security.events", "rih.error_class"),
            "planner_outcomes": total_by("rih.planner.outcomes", "rih.planner_status"),
        }

    def span(self, name: str, **attributes):
        return _Span(self.tracer, name, attributes)

    def shutdown(self) -> None:
        self.tracer_provider.shutdown()
        self.meter_provider.shutdown()


class _Span:
    def __init__(self, tracer, name, attributes):
        self._cm = tracer.start_as_current_span(name, attributes={k: v for k, v in attributes.items() if v is not None})

    def __enter__(self):
        self.span = self._cm.__enter__()
        return self.span

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            self.span.set_status(Status(StatusCode.ERROR))
            self.span.set_attribute("rih.error_class", "internal_error")
        return self._cm.__exit__(exc_type, exc, tb)


# ---------------------------------------------------------------- structured logs

_LOG_FIELD_ALLOWLIST = frozenset({
    "method", "route", "status", "duration_ms", "error_class", "request_id", "tool", "rule_id", "channel",
    "reason", "migrations_applied", "expired_owners_purged", "error_type", "incident", "scenario", "outcome",
    "trace_id", "span_id",
})


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line; only allowlisted structured fields are emitted."""

    def format(self, record: logging.LogRecord) -> str:
        from opentelemetry import trace as _trace

        doc: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + f".{int(record.msecs):03d}Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage()[:120],
        }
        fields = getattr(record, "fields", None) or {}
        for k, v in fields.items():
            if k in _LOG_FIELD_ALLOWLIST:
                doc[k] = v
        for k in ("reason", "migrations_applied", "expired_owners_purged", "error_type", "request_id"):
            if hasattr(record, k) and k not in doc:
                doc[k] = getattr(record, k)
        span = _trace.get_current_span()
        ctx = span.get_span_context() if span is not None else None
        if ctx is not None and ctx.is_valid:
            doc["trace_id"] = format(ctx.trace_id, "032x")
            doc["span_id"] = format(ctx.span_id, "016x")
        return json.dumps(doc, default=str)


def configure_json_logging(level: int = logging.INFO, stream=None, loggers: Iterable[str] = ("rih",)) -> None:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    for name in loggers:
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.setLevel(level)
        lg.propagate = False

from pathlib import Path
import json, time

LOG = Path("app/logs/audit.jsonl")

def log(event: str, level: str | None):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        "level": level,
        "version": "mvp1"
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

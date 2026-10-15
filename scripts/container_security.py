"""Container and repository security scans (Phase 8), run locally through Docker.

    python scripts/container_security.py --write

- Trivy image scan of rih-backend:local and rih-frontend:local (HIGH/CRITICAL, fixable only).
- Trivy misconfiguration scan of the Dockerfiles, Compose file and Kubernetes manifests.
- Gitleaks secret scan of the git history (read-only mount).
Fails (exit 1) on any fixable HIGH/CRITICAL vulnerability, HIGH/CRITICAL misconfiguration or
detected secret. Evidence: docs/evidence/containers/security-scan.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "containers" / "security-scan.json"
TRIVY = "aquasec/trivy:0.74.0"
GITLEAKS = "ghcr.io/gitleaks/gitleaks:v8.30.1"
CACHE = "rih-trivy-cache:/root/.cache/"
SOCK = "/var/run/docker.sock:/var/run/docker.sock"


def docker(*args, timeout=1800):
    p = subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def scan_image(image: str) -> dict:
    code, out, err = docker("run", "--rm", "-v", SOCK, "-v", CACHE, TRIVY, "image", "--quiet", "--format", "json",
                            "--severity", "HIGH,CRITICAL", "--ignore-unfixed", "--scanners", "vuln", image)
    if code != 0:
        return {"image": image, "status": "error", "detail": (err or out).strip()[-400:]}
    doc = json.loads(out)
    vulns = [v for r in doc.get("Results", []) for v in (r.get("Vulnerabilities") or [])]
    return {
        "image": image,
        "status": "pass" if not vulns else "fail",
        "high_critical_fixable": len(vulns),
        "findings": [{"id": v["VulnerabilityID"], "package": v["PkgName"], "installed": v.get("InstalledVersion"),
                      "fixed": v.get("FixedVersion"), "severity": v["Severity"]} for v in vulns][:50],
    }


def scan_config() -> dict:
    code, out, err = docker("run", "--rm", "-v", f"{ROOT}:/src:ro", "-v", CACHE, TRIVY, "config", "--quiet",
                            "--format", "json", "--severity", "HIGH,CRITICAL", "/src/deploy")
    code2, out2, err2 = docker("run", "--rm", "-v", f"{ROOT}:/src:ro", "-v", CACHE, TRIVY, "config", "--quiet",
                               "--format", "json", "--severity", "HIGH,CRITICAL", "/src/compose.yaml")
    findings = []
    for c, o, e in ((code, out, err), (code2, out2, err2)):
        if c != 0:
            return {"status": "error", "detail": (e or o).strip()[-400:]}
        for r in json.loads(o).get("Results", []) or []:
            for m in r.get("Misconfigurations") or []:
                if m.get("Status") == "FAIL":
                    findings.append({"target": r.get("Target"), "id": m.get("ID"), "title": m.get("Title"),
                                     "severity": m.get("Severity")})
    return {"status": "pass" if not findings else "fail", "high_critical": len(findings), "findings": findings}


def scan_secrets() -> dict:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="rih-gitleaks-") as tmp:
        code, out, err = docker("run", "--rm", "-v", f"{ROOT}:/repo:ro", "-v", f"{tmp}:/out", GITLEAKS, "git",
                                "/repo", "--no-banner", "--redact", "--config", "/repo/.gitleaks.toml",
                                "--report-format", "json", "--report-path", "/out/report.json", "--exit-code", "3")
        report = Path(tmp) / "report.json"
        found = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
    leaks = [{"rule": x.get("RuleID"), "file": x.get("File"), "commit": (x.get("Commit") or "")[:10]} for x in found]
    status = "pass" if code == 0 and not leaks else ("fail" if code == 3 or leaks else "error")
    summary = [ln for ln in (err or "").splitlines() if "commits scanned" in ln or "leaks" in ln]
    return {"status": status, "leaks": len(leaks), "findings": leaks[:20], "detail": " ".join(summary)[-300:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT))
    from scripts.redteam import git_commit

    report = {
        "report": "rih-container-security",
        "git_commit": git_commit(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tools": {"trivy": TRIVY, "gitleaks": GITLEAKS},
        "images": [scan_image("rih-backend:local"), scan_image("rih-frontend:local")],
        "config": scan_config(),
        "secrets": scan_secrets(),
    }
    statuses = [i["status"] for i in report["images"]] + [report["config"]["status"], report["secrets"]["status"]]
    report["status"] = "pass" if all(s == "pass" for s in statuses) else "fail"
    for i in report["images"]:
        print(f"{i['status'].upper():5s} image {i['image']}: {i.get('high_critical_fixable', i.get('detail'))}")
    print(f"{report['config']['status'].upper():5s} config: {report['config'].get('high_critical', report['config'].get('detail'))}")
    print(f"{report['secrets']['status'].upper():5s} secrets: {report['secrets'].get('leaks')} {report['secrets'].get('detail', '')}")
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

/** Maps a status word to a pill tone; the word itself is always shown next to the color. */
export function tone(value: string | null | undefined): string {
  switch (value) {
    case "approved": case "fresh": case "allowed": case "active": case "passed": case "pass": case "ok": case "ready":
    case "low": case "mitigated":
      return "pill pill--good";
    case "rejected": case "retired": case "expired": case "denied": case "disabled": case "failed": case "fail":
    case "high": case "critical": case "not_ready":
      return "pill pill--bad";
    case "baseline": case "pending": case "aging": case "stale": case "unknown": case "medium": case "moderate":
    case "blocked_pending_human_decision": case "skipped": case "quarantined": case "partially_mitigated":
    case "mitigating": case "open":
      return "pill pill--attention";
    default:
      return "pill";
  }
}

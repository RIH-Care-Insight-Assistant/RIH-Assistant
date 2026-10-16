"""A scripted Strands `Model` for offline tests and adversarial runs: it emits predetermined
tool calls or text.

It exercises the real Strands agent loop (tool specs, tool execution, results fed back)
without any network or model provider.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from strands.models import Model


class ScriptedModel(Model):
    def __init__(self, turns: List[Dict[str, Any]], *, delay_s: float = 0.0, fail: Exception | None = None):
        self.turns = list(turns)
        self.delay_s = delay_s
        self.fail = fail
        self.calls = 0
        self.seen_messages: List[Any] = []
        self.seen_tool_names: List[str] = []
        self.config: Dict[str, Any] = {}

    def update_config(self, **kw):
        self.config.update(kw)

    def get_config(self):
        return self.config

    async def structured_output(self, *a, **k):  # pragma: no cover - not used
        raise NotImplementedError
        yield

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        self.calls += 1
        self.seen_messages.append(json.loads(json.dumps(messages, default=str)))
        self.seen_tool_names = [s["name"] for s in (tool_specs or [])]
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.fail is not None:
            raise self.fail
        turn = self.turns.pop(0) if self.turns else {"text": "done"}
        yield {"messageStart": {"role": "assistant"}}
        if "tool" in turn:
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"t{self.calls}", "name": turn["tool"]}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(turn.get("args", {}))}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockDelta": {"delta": {"text": turn["text"]}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}

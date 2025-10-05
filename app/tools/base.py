from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolResult:
  text: str
  meta: Dict[str, Any]
  


class Tool:
    name: str = "tool"
    description: str = ""


    def run(self, payload: Dict[str, Any]) -> ToolResult: # override
          raise NotImplementedError

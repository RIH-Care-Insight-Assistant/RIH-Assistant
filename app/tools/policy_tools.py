
# File: app/tools/policy_tools.py (UNCHANGED)

from .base import Tool, ToolResult
from ..answer.compose import render_template

class TitleIXTool(Tool):
    name = "title_ix"
    description = "Provide Title IX information and contacts."

    def run(self, payload):
        return ToolResult(text=render_template("title_ix"), meta={})

class ConductTool(Tool):
    name = "conduct"
    description = "Provide Student Conduct/CARE information."

    def run(self, payload):
        return ToolResult(text=render_template("conduct"), meta={})

class RetentionTool(Tool):
    name = "retention"
    description = "Provide academic advising/retention resources."

    def run(self, payload):
        return ToolResult(text=render_template("retention"), meta={})

class CounselingTool(Tool):
    name = "counseling"
    description = "Provide counseling access info."

    def run(self, payload):
        return ToolResult(text=render_template("counseling"), meta={})

class CrisisTool(Tool):
    name = "crisis"
    description = "Provide crisis resources and stop."

    def run(self, payload):
        return ToolResult(text=render_template("crisis"), meta={"stop": True})

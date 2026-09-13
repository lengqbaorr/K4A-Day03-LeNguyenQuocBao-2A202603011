"""MCP Server cho AI Creative Director & Prompt Pipeline Optimizer."""

import json
import sys
from typing import Any, Dict, List

from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MCPGenerativePipelineServer:
    """Công bố và thực thi các tool GenAI qua response kiểu JSON-RPC 2.0."""

    def __init__(self, server_name: str = "genai-pipeline-optimizer-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách Tool Schemas cho LLM Provider."""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool và đóng gói kết quả theo cấu trúc JSON-RPC 2.0."""
        try:
            content = json.loads(dispatch_tool_call(tool_name, arguments))
        except json.JSONDecodeError as error:
            content = {
                "status": "MCP_ERROR",
                "message": f"Tool trả về JSON không hợp lệ: {error}"
            }

        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


# Alias giúp các phần code lab cũ vẫn import được trong quá trình chuyển đổi.
MCPAcademicServer = MCPGenerativePipelineServer


if __name__ == "__main__":
    server = MCPGenerativePipelineServer()
    print("==========================================================")
    print(f"🔌 MCP SERVER: {server.server_name}")
    print("==========================================================")
    print(f"📦 Tools: {[tool['name'] for tool in server.list_tools()]}")
    test_result = server.call_tool(
        "evaluate_model_cost_and_latency",
        {"task_complexity": "medium", "media_type": "multimodal"}
    )
    print(json.dumps(test_result, ensure_ascii=False, indent=2))

"""Web server tối giản cho giao diện chatbot GenAI Pipeline Optimizer."""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SRC_DIR))

from src.app import run_react_agent, save_waterfall_trace  # noqa: E402
from src.mcp_server import MCPGenerativePipelineServer  # noqa: E402
from src.providers import MockOfflineProvider, get_llm_provider  # noqa: E402


RUN_LOCK = threading.Lock()


def provider_info() -> dict[str, Any]:
    provider = get_llm_provider()
    return {
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "unknown"),
        "mode": "mock" if isinstance(provider, MockOfflineProvider) else "live"
    }


class ChatHandler(SimpleHTTPRequestHandler):
    """Phục vụ UI và endpoint POST /api/chat trên cùng origin."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    def _json_response(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/status":
            info = provider_info()
            info.update({"status": "ready", "mcp_server": "genai-pipeline-optimizer-mcp-server"})
            self._json_response(200, info)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._json_response(404, {"error": "Endpoint không tồn tại."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 100_000:
                raise ValueError("Kích thước request không hợp lệ.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            message = str(payload.get("message", "")).strip()
            if not message:
                raise ValueError("Vui lòng nhập creative brief.")

            provider = get_llm_provider()
            mcp_server = MCPGenerativePipelineServer()
            fallback_used = False
            requested_provider = provider.__class__.__name__
            with RUN_LOCK:
                trace = run_react_agent(message, provider, mcp_server)

            final_event = next(
                (event for event in reversed(trace) if event.get("action_type") == "FINAL_ANSWER"),
                {}
            )
            answer = final_event.get("output", "Agent chưa tạo được câu trả lời cuối cùng.")
            api_error = any(marker in answer for marker in (
                "API Error", "PERMISSION_DENIED", "Gemini Exception", "OpenAI Exception"
            ))
            if api_error and not isinstance(provider, MockOfflineProvider):
                fallback_used = True
                provider = MockOfflineProvider()
                with RUN_LOCK:
                    trace = run_react_agent(message, provider, mcp_server)
                final_event = next(
                    (event for event in reversed(trace) if event.get("action_type") == "FINAL_ANSWER"),
                    {}
                )
                answer = final_event.get("output", "Demo pipeline chưa tạo được kết quả.")

            save_waterfall_trace(trace)
            self._json_response(200, {
                "answer": answer,
                "trace": trace,
                "api_ok": True,
                "live_api_ok": not api_error,
                "fallback_used": fallback_used,
                "requested_provider": requested_provider,
                "provider": provider.__class__.__name__,
                "model": getattr(provider, "model_name", "unknown"),
                "mcp_server": mcp_server.server_name
            })
        except (ValueError, json.JSONDecodeError) as error:
            self._json_response(400, {"error": str(error)})
        except Exception as error:
            self._json_response(500, {"error": f"Không thể xử lý yêu cầu: {error}"})

    def log_message(self, format_string: str, *args) -> None:
        print(f"[WEB] {self.address_string()} - {format_string % args}")


def main() -> None:
    host = "127.0.0.1"
    port = int(os.getenv("DEMO_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ChatHandler)
    print("==========================================================")
    print("🎨 CREATIVE FLOW AI — WEB CHATBOT")
    print("==========================================================")
    print(f"Mở trình duyệt tại: http://{host}:{port}")
    print("Nhấn Ctrl+C để dừng server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng demo server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

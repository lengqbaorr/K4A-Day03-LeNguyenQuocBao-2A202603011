"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()


def _sanitize_schema_for_gemini(value):
    """Loại JSON Schema keyword mà Gemini Function Calling chưa hỗ trợ."""
    if isinstance(value, dict):
        return {
            key: _sanitize_schema_for_gemini(item)
            for key, item in value.items()
            if key not in {"additionalProperties", "$schema"}
        }
    if isinstance(value, list):
        return [_sanitize_schema_for_gemini(item) for item in value]
    return value

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Mock Provider cho phép kiểm tra ReAct loop mà không tốn API."""

    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (
            "[Mock Chatbot Response]: Tôi có thể đề xuất ý tưởng nội dung, "
            "nhưng baseline không thể tra cứu vận hành hoặc kích hoạt pipeline."
        )

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        request_lower = prompt_lower.split("quy trình bắt buộc:", 1)[0]
        last_action = ""
        if "action step" in prompt_lower:
            last_action = prompt_lower.rsplit("action step", 1)[-1].splitlines()[0]

        if "execute_generative_pipeline" in last_action:
            return {
                "type": "text",
                "content": (
                    "## Pipeline sáng tạo đã hoàn tất\n\n"
                    "MCP đã điều phối các agent theo workflow được chọn. "
                    "Caption và media mẫu nằm trong phần kết quả bên dưới.\n\n"
                    "Nội dung hiện ở chế độ **chờ duyệt** và chưa được đăng thật."
                ),
                "thought": "Đã có Observation thành công từ pipeline, tôi tổng hợp kết quả."
            }

        if "evaluate_model_cost_and_latency" in last_action:
            high_complexity = '"task_complexity": "high"' in prompt_lower
            text_only = '"media_type": "text"' in prompt_lower
            video_requested = '"media_type": "video"' in prompt_lower
            return {
                "type": "tool_call",
                "tool_name": "execute_generative_pipeline",
                "arguments": {
                    "workflow_json": {
                        "campaign_name": "Chiến dịch GenAI",
                        "objective": "Tạo nội dung truyền thông theo brief người dùng",
                        "target_audience": "Khách hàng mục tiêu trong brief",
                        "channels": ["Email"] if text_only else ["Facebook", "Instagram"],
                        "text_model": "Claude" if high_complexity else "GPT",
                        "image_model": (
                            "none" if text_only
                            else ("Midjourney" if high_complexity else "Stable Diffusion")
                        ),
                        "video_model": "Runway" if video_requested else "none",
                        "deliverables": (
                            ["caption"] if text_only
                            else (
                                ["caption", "poster", "video", "facebook_post"]
                                if video_requested
                                else ["caption", "poster", "facebook_post"]
                            )
                        ),
                        "publish_mode": "review_required"
                    }
                },
                "thought": "Dùng kết quả tra cứu để cấu hình và kích hoạt pipeline."
            }

        complexity = "high" if any(
            marker in request_lower
            for marker in ["cao cấp", "toàn quốc", "đa kênh", "phức tạp"]
        ) else "medium"
        if any(marker in request_lower for marker in ["video", "reel", "tiktok"]):
            media = "video"
        elif any(
            marker in request_lower
            for marker in ["chỉ văn bản", "text-only", "email campaign"]
        ):
            media = "text"
        else:
            media = "multimodal"
        return {
            "type": "tool_call",
            "tool_name": "evaluate_model_cost_and_latency",
            "arguments": {
                "task_complexity": complexity,
                "media_type": media
            },
            "thought": "Cần tra cứu chi phí, độ trễ và hạn ngạch trước khi chọn model."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return {
                "type": "text",
                "content": "[Gemini API Error]: Chưa cấu hình GEMINI_API_KEY hợp lệ.",
                "thought": "Không thể gọi Gemini vì thiếu thông tin xác thực."
            }
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": _sanitize_schema_for_gemini(
                        tool.get("parameters", {})
                    )
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Error]: {str(e)}")
            return {
                "type": "text",
                "content": f"[Gemini API Error]: {str(e)}",
                "thought": "Gemini API từ chối hoặc không thể xử lý request; không fallback sang Mock."
            }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return {
                "type": "text",
                "content": "[OpenAI API Error]: Chưa cấu hình OPENAI_API_KEY hợp lệ.",
                "thought": "Không thể gọi OpenAI vì thiếu thông tin xác thực."
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Error]: {str(e)}")
            return {
                "type": "text",
                "content": f"[OpenAI API Error]: {str(e)}",
                "thought": "OpenAI API từ chối hoặc không thể xử lý request; không fallback sang Mock."
            }


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()

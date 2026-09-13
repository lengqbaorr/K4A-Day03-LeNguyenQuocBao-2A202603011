"""
🚀 AI CREATIVE DIRECTOR & PROMPT PIPELINE OPTIMIZER
ReAct Agent tối ưu model, prompt và quy trình sinh nội dung Media & Design.
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPGenerativePipelineServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(
    user_query: str,
    provider,
    mcp_server: MCPGenerativePipelineServer
) -> list:
    """Chạy ReAct loop cho Trợ lý Tối ưu Quy trình GenAI."""
    print(f"\n🤖 [GENAI PIPELINE AGENT] Yêu cầu: {user_query}")

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    called_tools = []
    last_observation = {}

    # Provider nhận prompt dạng chuỗi nên Action và Observation được tích lũy
    # vào context để LLM có đủ dữ liệu quyết định ở lượt tiếp theo.
    conversation_context = f"""
YÊU CẦU CHIẾN DỊCH:
{user_query}

QUY TRÌNH BẮT BUỘC:
1. Phân tích brief và gọi evaluate_model_cost_and_latency.
2. Dựa vào Observation để chọn GPT/Claude, Midjourney/Stable Diffusion và
   Runway nếu brief cần video.
3. Tạo workflow_json và gọi execute_generative_pipeline.
4. Khi pipeline hoàn tất, trả về type='text' để tổng kết.
Không tự bịa chi phí, độ trễ, hạn ngạch hoặc kết quả pipeline.
""".strip()

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        llm_response = provider.generate_with_tools(
            conversation_context,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        thought = llm_response.get("thought", "Đang suy luận...")
        response_type = llm_response.get("type")
        print(f"🧠 [Thought]: {thought}")

        # Trường hợp 1: LLM đã có đủ dữ liệu để kết luận.
        if response_type == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Trường hợp 2: LLM đề xuất một Tool Call.
        if response_type == "tool_call":
            tool_name = llm_response.get("tool_name", "")
            arguments = llm_response.get("arguments", {})
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            # Pipeline chỉ được chạy sau khi đã quan sát kết quả tra cứu model.
            if (
                tool_name == "execute_generative_pipeline"
                and "evaluate_model_cost_and_latency" not in called_tools
            ):
                obs_data = {
                    "status": "POLICY_ERROR",
                    "message": (
                        "Phải gọi evaluate_model_cost_and_latency thành công "
                        "trước khi chạy pipeline."
                    )
                }
            elif tool_name in called_tools:
                obs_data = {
                    "status": "POLICY_ERROR",
                    "message": f"Tool '{tool_name}' đã được gọi, không gọi lặp lại."
                }
            else:
                mcp_result = mcp_server.call_tool(tool_name, arguments)
                obs_data = mcp_result.get("result", {})
                if obs_data:
                    called_tools.append(tool_name)
                else:
                    obs_data = {
                        "status": "MCP_ERROR",
                        "message": "MCP Server không trả về Observation."
                    }

            last_observation = obs_data
            print(
                "👁️ [Observation từ MCP Server]: "
                f"{json.dumps(obs_data, ensure_ascii=False)}"
            )
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            status = obs_data.get("status")
            if status not in {"SUCCESS", "POLICY_ERROR"}:
                final_answer = obs_data.get(
                    "message",
                    "Không thể hoàn tất pipeline do công cụ trả về lỗi."
                )
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Dừng an toàn do Tool Execution thất bại.",
                    "output": final_answer,
                    "latency_ms": 0.0
                })
                break

            # Không dừng sau Tool Call: nạp Observation cho lượt suy luận kế tiếp.
            conversation_context += (
                f"\n\nACTION STEP {step}: {tool_name}"
                f"\nARGUMENTS: {json.dumps(arguments, ensure_ascii=False)}"
                f"\nOBSERVATION: {json.dumps(obs_data, ensure_ascii=False)}"
                "\nHãy tiếp tục đúng quy trình và không gọi lại tool đã hoàn tất."
            )
            if tool_name == "execute_generative_pipeline" and status == "SUCCESS":
                conversation_context += (
                    "\nPipeline đã hoàn tất. Lượt kế tiếp phải trả về type='text', "
                    "nêu model và lý do lựa chọn, chi phí ước tính, độ trễ, "
                    "hạn ngạch còn lại, run_id, trạng thái, artifacts và nói rõ "
                    "đây là mô phỏng nếu chưa kết nối API media/social thật."
                )
            continue

        # Bảo vệ khi Provider trả về response không đúng giao ước.
        final_answer = "LLM Provider trả về response type không hợp lệ."
        print(f"🏁 [Final Answer]: {final_answer}")
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Không xác định được Action từ phản hồi LLM.",
            "output": final_answer,
            "latency_ms": latency_ms
        })
        break

    else:
        final_answer = (
            "Agent đạt giới hạn vòng lặp trước khi hoàn tất pipeline. "
            f"Observation cuối: {json.dumps(last_observation, ensure_ascii=False)}"
        )
        print(f"🏁 [Final Answer]: {final_answer}")
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Dừng do đạt MAX_ITERATIONS.",
            "output": final_answer,
            "latency_ms": 0.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🎨 AI CREATIVE DIRECTOR & PROMPT PIPELINE OPTIMIZER")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPGenerativePipelineServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện với GenAI Pipeline Agent:")
        print("💡 Gợi ý yêu cầu thử nghiệm:")
        print("   - 'Tạo chiến dịch Facebook ra mắt sản phẩm cà phê mới.'")
        print("   - 'Tạo email campaign chỉ có văn bản với ngân sách thấp.'")
        print("   - 'Thiết kế chiến dịch đa kênh chất lượng cao gồm caption và key visual.'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Nhập brief chiến dịch: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print("--- 🏁 DEMO CHẠY THỬ MỘT BRIEF CHIẾN DỊCH MẪU ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")

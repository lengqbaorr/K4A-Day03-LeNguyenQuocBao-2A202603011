# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Lê Nguyễn Quốc Bảo  
> **Mã Sinh Viên / Mã Học viên:** 2A202603011  
> **Chủ đề Lựa chọn:** AI Creative Director & Prompt Pipeline Optimizer (Trợ lý Tối ưu Quy trình & Prompt Engineering cho Media & Design) 

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | Agent phải phân tích brief truyền thông, xác định mục tiêu, đối tượng, kênh và loại media; đánh giá độ phức tạp; tra cứu model; so sánh chi phí, hạn ngạch và độ trễ; chọn tổ hợp model; thiết kế prompt/workflow; sau đó mới kích hoạt pipeline sinh nội dung. Đây là chuỗi suy luận nhiều bước có quan hệ phụ thuộc rõ ràng. |
| **2. Tool Interaction** | 5 / 5 | Hệ thống cần kết nối MCP Server để gọi `evaluate_model_cost_and_latency(task_complexity, media_type)` nhằm lấy dữ liệu vận hành của các model và gọi `execute_generative_pipeline(workflow_json)` để kích hoạt luồng sinh text, sinh ảnh, ghép caption và chuẩn bị xuất bản. |
| **3. Dynamic Decision** | 5 / 5 | Quyết định chọn GPT hay Claude và Midjourney hay Stable Diffusion phụ thuộc trực tiếp vào loại media, độ phức tạp, hạn ngạch, chi phí và độ trễ do Tool 1 trả về. Workflow ở bước sau phải được điều chỉnh theo Observation thực tế thay vì dùng một cấu hình cố định. |
| **4. Long Horizon Goal** | 4 / 5 | Agent phải duy trì xuyên suốt mục tiêu chiến dịch, chân dung khách hàng, thông điệp, kênh truyền thông, yêu cầu đầu ra và ràng buộc ngân sách từ brief ban đầu đến lúc hoàn tất pipeline. Phạm vi một chiến dịch tương đối dài nhưng chưa yêu cầu tự vận hành, theo dõi và tối ưu liên tục trong nhiều ngày. |
| **TỔNG ĐIỂM AGENTIC FIT** | **19 / 20** | *Tổng điểm lớn hơn 12/20: Đề tài rất phù hợp triển khai dưới dạng Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dưới đây là cấu trúc Waterfall Trace dự kiến dùng để nghiệm thu. Đoạn log thực tế sẽ được thay thế sau khi chạy test suite với LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Tạo chiến dịch Facebook và Instagram ra mắt cà phê rang xay Mộc Nhiên cho người trẻ 22-30 tuổi, gồm caption và key visual, ngân sách GenAI tiết kiệm.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "evaluate_model_cost_and_latency",
    "arguments": {
      "task_complexity": "medium",
      "media_type": "multimodal"
    },
    "observation": {
      "status": "SUCCESS",
      "task_complexity": "medium",
      "media_type": "multimodal",
      "candidates": [
        {
          "model": "GPT",
          "estimated_cost_usd": 0.08,
          "estimated_latency_ms": 1800,
          "api_quota_remaining": 850
        },
        {
          "model": "Claude",
          "estimated_cost_usd": 0.1,
          "estimated_latency_ms": 2100,
          "api_quota_remaining": 620
        },
        {
          "model": "Stable Diffusion",
          "estimated_cost_usd": 0.03,
          "estimated_latency_ms": 4200,
          "api_quota_remaining": 300
        },
        {
          "model": "Midjourney",
          "estimated_cost_usd": 0.08,
          "estimated_latency_ms": 9000,
          "api_quota_remaining": 120
        }
      ],
      "recommendation": {
        "text_model": "GPT",
        "image_model": "Stable Diffusion",
        "selection_strategy": "cost_latency_balanced"
      }
    },
    "latency_ms": 5812.28
  },
  {
    "step": 2,
    "query": "Tạo chiến dịch Facebook và Instagram ra mắt cà phê rang xay Mộc Nhiên cho người trẻ 22-30 tuổi, gồm caption và key visual, ngân sách GenAI tiết kiệm.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "execute_generative_pipeline",
    "arguments": {
      "workflow_json": {
        "publish_mode": "review_required",
        "deliverables": [
          "caption",
          "key visual"
        ],
        "campaign_name": "Ra mắt cà phê rang xay Mộc Nhiên",
        "target_audience": "Người trẻ 22-30 tuổi",
        "text_model": "GPT",
        "channels": [
          "Facebook",
          "Instagram"
        ],
        "objective": "Ra mắt sản phẩm cà phê rang xay Mộc Nhiên cho người trẻ 22-30 tuổi với ngân sách tiết kiệm",
        "image_model": "Stable Diffusion"
      }
    },
    "observation": {
      "status": "SUCCESS",
      "run_id": "GEN-8D66708A0B",
      "campaign_name": "Ra mắt cà phê rang xay Mộc Nhiên",
      "pipeline_status": "COMPLETED",
      "pipeline_steps": [
        {
          "step": "generate_text",
          "model": "GPT",
          "status": "COMPLETED"
        },
        {
          "step": "generate_image",
          "model": "Stable Diffusion",
          "status": "COMPLETED"
        },
        {
          "step": "merge_caption",
          "status": "COMPLETED"
        },
        {
          "step": "prepare_publication",
          "mode": "review_required",
          "status": "DRAFT_READY"
        }
      ],
      "artifacts": [
        {
          "type": "caption",
          "status": "READY"
        },
        {
          "type": "key visual",
          "status": "READY"
        }
      ],
      "message": "Pipeline đã hoàn tất. Nội dung đang ở trạng thái bản nháp và cần được duyệt trước khi xuất bản."
    },
    "latency_ms": 4008.38
  },
  {
    "step": 3,
    "query": "Tạo chiến dịch Facebook và Instagram ra mắt cà phê rang xay Mộc Nhiên cho người trẻ 22-30 tuổi, gồm caption và key visual, ngân sách GenAI tiết kiệm.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Chiến dịch ra mắt cà phê rang xay **Mộc Nhiên** đã được xử lý thành công thông qua Generative Pipeline. Dưới đây là thông tin chi tiết:\n\n* **Model đã chọn:**\n  * **Text Model:** GPT (Tối ưu chi phí & độ trễ)\n  * **Image Model:** Stable Diffusion (Tiết kiệm ngân sách)\n* **Run ID:** `GEN-8D66708A0B`\n* **Trạng thái Pipeline:** `COMPLETED` (Bản nháp đã sẵn sàng, chờ duyệt - `review_required`)\n* **Sản phẩm truyền thông (Artifacts) đã tạo:**\n  1. **Caption** (Trạng thái: `READY`) - Phù hợp kênh Facebook & Instagram hướng tới giới trẻ 22-30 tuổi.\n  2. **Key Visual** (Trạng thái: `READY`) - Hình ảnh thiết kế riêng cho chiến dịch.\n\nNội dung hiện đang ở dạng bản nháp và chờ phê duyệt trước khi tiến hành xuất bản chính thức.",
    "latency_ms": 5392.45
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI). *(Chưa thực hiện trong giai đoạn brainstorm.)*
- **Tổng số Test Cases đã chạy thành công:** Chưa chạy / 5 test cases *(mục tiêu dự kiến: 5/5).*
- **Số lượt gọi Tool qua MCP Server chính xác:** Chưa xác minh *(dự kiến 10 lượt cho 5 test cases, mỗi test gọi 2 tool).*
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!

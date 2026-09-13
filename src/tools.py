"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Khai báo Tool Schemas và Execution Layer cho đề tài:
AI Creative Director & Prompt Pipeline Optimizer.
"""

import hashlib
import json
from typing import Any, Dict


# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "evaluate_model_cost_and_latency",
        "description": (
            "Tra cứu hạn ngạch API, chi phí ước tính và độ trễ của các model "
            "GenAI phù hợp với độ phức tạp và loại media của chiến dịch."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Độ phức tạp của yêu cầu: low, medium hoặc high."
                },
                "media_type": {
                    "type": "string",
                    "enum": ["text", "image", "video", "multimodal"],
                    "description": "Loại nội dung cần sinh: text, image, video hoặc multimodal."
                }
            },
            "required": ["task_complexity", "media_type"],
            "additionalProperties": False
        }
    },
    {
        "name": "execute_generative_pipeline",
        "description": (
            "Kích hoạt workflow tự động nối các bước sinh text, sinh ảnh, ghép "
            "caption và tạo bản nháp xuất bản cho chiến dịch truyền thông."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_json": {
                    "type": "object",
                    "description": "Đặc tả workflow sinh nội dung cần thực thi.",
                    "properties": {
                        "campaign_name": {
                            "type": "string",
                            "description": "Tên chiến dịch truyền thông."
                        },
                        "objective": {
                            "type": "string",
                            "description": "Mục tiêu chính của chiến dịch."
                        },
                        "target_audience": {
                            "type": "string",
                            "description": "Nhóm khách hàng mục tiêu."
                        },
                        "channels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "description": "Danh sách kênh phát hành nội dung."
                        },
                        "text_model": {
                            "type": "string",
                            "enum": ["GPT", "Claude"],
                            "description": "Model dùng để sinh nội dung văn bản."
                        },
                        "image_model": {
                            "type": "string",
                            "enum": ["Midjourney", "Stable Diffusion", "none"],
                            "description": "Model sinh ảnh; dùng none cho chiến dịch chỉ có văn bản."
                        },
                        "video_model": {
                            "type": "string",
                            "enum": ["Runway", "none"],
                            "description": "Model sinh video; dùng none nếu workflow không cần video."
                        },
                        "deliverables": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "description": "Danh sách sản phẩm truyền thông cần tạo."
                        },
                        "publish_mode": {
                            "type": "string",
                            "enum": ["draft", "review_required"],
                            "description": "Chế độ tạo bản nháp hoặc chờ duyệt trước khi xuất bản."
                        }
                    },
                    "required": [
                        "campaign_name",
                        "objective",
                        "target_audience",
                        "channels",
                        "text_model",
                        "image_model",
                        "video_model",
                        "deliverables",
                        "publish_mode"
                    ],
                    "additionalProperties": False
                }
            },
            "required": ["workflow_json"],
            "additionalProperties": False
        }
    }
]


# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

# Dữ liệu phục vụ bài lab, mô phỏng catalog vận hành của các model GenAI.
# Chi phí là ước tính cho một lần sinh nội dung, không phải bảng giá thương mại thật.
MOCK_MODEL_DATABASE = {
    "GPT": {
        "supported_media": ["text", "image", "video", "multimodal"],
        "supported_complexity": ["low", "medium", "high"],
        "estimated_cost_usd": {"low": 0.02, "medium": 0.08, "high": 0.24},
        "estimated_latency_ms": 1800,
        "api_quota_remaining": 850
    },
    "Claude": {
        "supported_media": ["text", "image", "video", "multimodal"],
        "supported_complexity": ["medium", "high"],
        "estimated_cost_usd": {"low": 0.03, "medium": 0.10, "high": 0.30},
        "estimated_latency_ms": 2100,
        "api_quota_remaining": 620
    },
    "Stable Diffusion": {
        "supported_media": ["image", "video", "multimodal"],
        "supported_complexity": ["low", "medium", "high"],
        "estimated_cost_usd": {"low": 0.01, "medium": 0.03, "high": 0.07},
        "estimated_latency_ms": 4200,
        "api_quota_remaining": 300
    },
    "Midjourney": {
        "supported_media": ["image", "video", "multimodal"],
        "supported_complexity": ["medium", "high"],
        "estimated_cost_usd": {"low": 0.04, "medium": 0.08, "high": 0.15},
        "estimated_latency_ms": 9000,
        "api_quota_remaining": 120
    },
    "Runway": {
        "supported_media": ["video", "multimodal"],
        "supported_complexity": ["low", "medium", "high"],
        "estimated_cost_usd": {"low": 0.12, "medium": 0.35, "high": 0.80},
        "estimated_latency_ms": 18000,
        "api_quota_remaining": 60
    }
}


def execute_evaluate_model_cost_and_latency(
    task_complexity: str,
    media_type: str
) -> str:
    """Tra cứu model phù hợp và đề xuất tổ hợp tối ưu."""
    complexity = task_complexity.strip().lower()
    media = media_type.strip().lower()

    if complexity not in {"low", "medium", "high"}:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "task_complexity phải là low, medium hoặc high."
        }, ensure_ascii=False)

    if media not in {"text", "image", "video", "multimodal"}:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "media_type phải là text, image, video hoặc multimodal."
        }, ensure_ascii=False)

    candidates = []
    for model_name, model_data in MOCK_MODEL_DATABASE.items():
        if (
            media in model_data["supported_media"]
            and complexity in model_data["supported_complexity"]
            and model_data["api_quota_remaining"] > 0
        ):
            candidates.append({
                "model": model_name,
                "estimated_cost_usd": model_data["estimated_cost_usd"][complexity],
                "estimated_latency_ms": model_data["estimated_latency_ms"],
                "api_quota_remaining": model_data["api_quota_remaining"]
            })

    text_candidates = [
        item for item in candidates if item["model"] in {"GPT", "Claude"}
    ]
    image_candidates = [
        item for item in candidates
        if item["model"] in {"Midjourney", "Stable Diffusion"}
    ]
    video_candidates = [
        item for item in candidates if item["model"] == "Runway"
    ]

    if complexity == "high":
        text_model = _prefer_model(text_candidates, "Claude")
        image_model = _prefer_model(image_candidates, "Midjourney")
        video_model = _prefer_model(video_candidates, "Runway") if media == "video" else None
        strategy = "quality_first"
    else:
        text_model = _select_lowest_cost(text_candidates)
        image_model = _select_lowest_cost(image_candidates)
        video_model = _select_lowest_cost(video_candidates) if media == "video" else None
        strategy = "cost_latency_balanced"

    return json.dumps({
        "status": "SUCCESS",
        "task_complexity": complexity,
        "media_type": media,
        "candidates": candidates,
        "recommendation": {
            "text_model": text_model,
            "image_model": image_model or "none",
            "video_model": video_model or "none",
            "selection_strategy": strategy
        }
    }, ensure_ascii=False)


def _prefer_model(candidates: list, preferred_name: str):
    """Chọn model ưu tiên nếu khả dụng, nếu không chọn ứng viên đầu tiên."""
    for candidate in candidates:
        if candidate["model"] == preferred_name:
            return preferred_name
    return candidates[0]["model"] if candidates else None


def _select_lowest_cost(candidates: list):
    """Chọn model có chi phí thấp nhất, dùng độ trễ để phá hòa."""
    if not candidates:
        return None
    selected = min(
        candidates,
        key=lambda item: (
            item["estimated_cost_usd"],
            item["estimated_latency_ms"]
        )
    )
    return selected["model"]


def execute_generative_pipeline(workflow_json: Dict[str, Any]) -> str:
    """Kiểm tra workflow và mô phỏng quá trình sinh nội dung truyền thông."""
    if not isinstance(workflow_json, dict):
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "workflow_json phải là một JSON object."
        }, ensure_ascii=False)

    required_fields = {
        "campaign_name",
        "objective",
        "target_audience",
        "channels",
        "text_model",
        "image_model",
        "video_model",
        "deliverables",
        "publish_mode"
    }
    missing_fields = sorted(required_fields - workflow_json.keys())
    if missing_fields:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": f"Workflow thiếu trường bắt buộc: {', '.join(missing_fields)}."
        }, ensure_ascii=False)

    if workflow_json["text_model"] not in {"GPT", "Claude"}:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "text_model phải là GPT hoặc Claude."
        }, ensure_ascii=False)

    if workflow_json["image_model"] not in {
        "Midjourney", "Stable Diffusion", "none"
    }:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "image_model phải là Midjourney, Stable Diffusion hoặc none."
        }, ensure_ascii=False)

    if workflow_json["video_model"] not in {"Runway", "none"}:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "video_model phải là Runway hoặc none."
        }, ensure_ascii=False)

    if workflow_json["publish_mode"] not in {"draft", "review_required"}:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "publish_mode phải là draft hoặc review_required."
        }, ensure_ascii=False)

    canonical_workflow = json.dumps(
        workflow_json,
        ensure_ascii=False,
        sort_keys=True
    )
    run_id = "GEN-" + hashlib.sha256(
        canonical_workflow.encode("utf-8")
    ).hexdigest()[:10].upper()

    complexity = (
        "high"
        if workflow_json["text_model"] == "Claude"
        or workflow_json["image_model"] == "Midjourney"
        else "medium"
    )
    deliverable_text = " ".join(workflow_json["deliverables"]).lower()
    channels_text = " ".join(workflow_json["channels"]).lower()
    campaign_name = workflow_json["campaign_name"]
    target_audience = workflow_json["target_audience"]

    pipeline_steps = []
    generated_content = {}

    text_cost = MOCK_MODEL_DATABASE[workflow_json["text_model"]][
        "estimated_cost_usd"
    ][complexity]
    pipeline_steps.append({
        "step": "generate_caption",
        "agent": "Copywriter Agent",
        "model": workflow_json["text_model"],
        "mcp_action": "generate_text",
        "estimated_cost_usd": text_cost,
        "status": "COMPLETED"
    })
    generated_content["caption"] = (
        f"✨ {campaign_name}\n\n"
        f"Một trải nghiệm được thiết kế dành cho {target_audience}. "
        "Khám phá ngay hôm nay và chia sẻ khoảnh khắc của bạn!\n\n"
        "#CreativeCampaign #AIGenerated #HumanApproved"
    )

    if workflow_json["image_model"] != "none":
        image_cost = MOCK_MODEL_DATABASE[workflow_json["image_model"]][
            "estimated_cost_usd"
        ][complexity]
        pipeline_steps.append({
            "step": "generate_poster",
            "agent": "Poster Design Agent",
            "model": workflow_json["image_model"],
            "mcp_action": "generate_image",
            "estimated_cost_usd": image_cost,
            "status": "COMPLETED"
        })
        generated_content["poster"] = {
            "headline": campaign_name,
            "subheadline": "Thiết kế bởi AI · Hoàn thiện bởi con người",
            "visual_prompt": (
                f"Premium advertising poster for {campaign_name}, "
                f"target audience: {target_audience}, editorial composition, "
                "studio lighting, brand-safe, social media format 4:5"
            ),
            "format": "1080 × 1350",
            "simulation": True
        }

    if workflow_json["video_model"] != "none" or "video" in deliverable_text:
        video_model = (
            workflow_json["video_model"]
            if workflow_json["video_model"] != "none"
            else "Runway"
        )
        video_cost = MOCK_MODEL_DATABASE[video_model]["estimated_cost_usd"][complexity]
        pipeline_steps.append({
            "step": "generate_video",
            "agent": "Video Creative Agent",
            "model": video_model,
            "mcp_action": "generate_video",
            "estimated_cost_usd": video_cost,
            "status": "COMPLETED"
        })
        generated_content["video"] = {
            "duration_seconds": 15,
            "format": "1080 × 1920",
            "storyboard": [
                "0–3s: Brand hook và chuyển động mở đầu",
                "3–10s: Sản phẩm, lợi ích và bối cảnh sử dụng",
                "10–15s: Call-to-action và logo chiến dịch"
            ],
            "simulation": True
        }

    pipeline_steps.append({
        "step": "assemble_media",
        "agent": "Media Assembly Agent",
        "mcp_action": "merge_caption_and_media",
        "estimated_cost_usd": 0.01,
        "status": "COMPLETED"
    })

    wants_facebook = "facebook" in channels_text or "facebook" in deliverable_text
    publication = {
        "channel": "Facebook" if wants_facebook else workflow_json["channels"][0],
        "status": "SIMULATED_READY_TO_PUBLISH",
        "caption_attached": True,
        "poster_attached": "poster" in generated_content,
        "video_attached": "video" in generated_content,
        "external_side_effect": False,
        "approval": workflow_json["publish_mode"]
    }
    pipeline_steps.append({
        "step": "publish_social_post",
        "agent": "Social Publisher Agent",
        "mcp_action": "publish_facebook_post" if wants_facebook else "prepare_social_post",
        "estimated_cost_usd": 0.0,
        "mode": "SIMULATION",
        "status": "READY_FOR_HUMAN_APPROVAL"
    })

    pipeline_cost = round(sum(
        float(item.get("estimated_cost_usd", 0)) for item in pipeline_steps
    ), 4)

    return json.dumps({
        "status": "SUCCESS",
        "run_id": run_id,
        "campaign_name": campaign_name,
        "pipeline_status": "COMPLETED",
        "pipeline_steps": pipeline_steps,
        "artifacts": [
            {"type": item, "status": "READY"}
            for item in workflow_json["deliverables"]
        ],
        "generated_content": generated_content,
        "publication": publication,
        "pipeline_cost_usd": pipeline_cost,
        "execution_mode": "SIMULATION",
        "message": (
            "MCP pipeline demo đã tạo caption và media, sau đó chuẩn bị bài đăng. "
            "Không có nội dung nào được đăng thật; cần người dùng duyệt trước."
        )
    }, ensure_ascii=False)


# ==============================================================================
# 3. TOOL ROUTER
# ==============================================================================

TOOL_ROUTER = {
    "evaluate_model_cost_and_latency": execute_evaluate_model_cost_and_latency,
    "execute_generative_pipeline": execute_generative_pipeline
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Trung chuyển yêu cầu thực thi tới đúng tool backend."""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except TypeError as error:
            return json.dumps({
                "status": "VALIDATION_ERROR",
                "error": str(error)
            }, ensure_ascii=False)
        except Exception as error:
            return json.dumps({
                "status": "EXECUTION_ERROR",
                "error": str(error)
            }, ensure_ascii=False)

    return json.dumps({
        "status": "UNKNOWN_TOOL",
        "error": f"Tool '{tool_name}' không tồn tại."
    }, ensure_ascii=False)

"""
PaddleOCR API 中间件
在 agent 开始推理前，自动对输入图片执行 OCR 解析，
将简化后的结构化结果注入到 messages 中供 agent 使用。
"""

import os
import json
import asyncio
import logging
from typing import Any

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import HumanMessage
from langgraph.runtime import Runtime

from config import STRUCT_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)


class OCRMiddleware(AgentMiddleware):
    """PaddleOCR before_agent 中间件

    功能：
    1. 从 state 中读取 image_paths（由 workflow prepare_input 节点写入）
    2. 调用 PaddleOCR API 异步解析所有图片（含重试逻辑）
    3. 简化 OCR 结果（只保留 block_label, block_content, block_order）
    4. 将简化结果作为 HumanMessage 注入 agent 的 messages

    使用方式：
        agent = create_deep_agent(
            ...,
            middleware=[OCRMiddleware()],
        )
    """

    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """agent 启动前执行 OCR 解析"""
        print("[OCRMiddleware] before_agent 被调用")

        messages = state.get("messages", [])
        print(f"[OCRMiddleware] messages 数量: {len(messages)}")
        if not messages:
            print("[OCRMiddleware] 无 messages，跳过")
            return None

        # 从最后一条用户消息中提取图片路径
        last_msg = messages[-1]
        print(f"[OCRMiddleware] last_msg type: {type(last_msg).__name__}")
        print(f"[OCRMiddleware] last_msg: {repr(last_msg)[:200]}")
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        print(f"[OCRMiddleware] content[:200]: {content[:200]}")

        # 尝试解析 JSON 格式的图片路径列表
        image_paths = self._extract_image_paths(content)
        if not image_paths:
            print("[OCRMiddleware] 未检测到图片路径，跳过 OCR")
            logger.info("OCRMiddleware: 未检测到图片路径，跳过 OCR")
            return None

        print(f"[OCRMiddleware] 检测到 {len(image_paths)} 张图片，开始 OCR 解析")
        logger.info(f"OCRMiddleware: 检测到 {len(image_paths)} 张图片，开始 OCR 解析")

        # 执行 OCR
        try:
            ocr_results = self._run_ocr(image_paths)
        except Exception as e:
            logger.error(f"OCRMiddleware: OCR 解析失败: {e}")
            error_msg = HumanMessage(content=f"OCR 解析失败: {str(e)}，请检查 PaddleOCR API 状态。")
            return {"messages": messages + [error_msg]}

        # 简化 OCR 结果
        simplified = self._simplify_results(ocr_results)

        # 保存 agent_input.json
        os.makedirs(RESULTS_DIR, exist_ok=True)
        agent_input_path = os.path.join(RESULTS_DIR, "agent_input.json")
        with open(agent_input_path, 'w', encoding='utf-8') as f:
            json.dump(simplified, f, ensure_ascii=False, indent=2)
        logger.info(f"OCRMiddleware: Agent 输入数据已保存到 {agent_input_path}")

        # 构造注入消息
        total_blocks = sum(len(r.get("blocks", [])) for r in simplified)
        ocr_message = HumanMessage(content=(
            f"OCR 解析完成，共 {len(simplified)} 页，{total_blocks} 个 block。\n\n"
            f"OCR数据: {json.dumps(simplified, ensure_ascii=False)}"
        ))

        # 替换原始消息（图片路径）为 OCR 结果
        new_messages = messages[:-1] + [ocr_message]
        return {"messages": new_messages}

    def _extract_image_paths(self, content: str) -> list[str]:
        """从消息内容中提取图片路径列表"""
        try:
            data = json.loads(content)
            if isinstance(data, list) and all(isinstance(p, str) for p in data):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def _run_ocr(self, image_paths: list[str]) -> list[dict]:
        """执行 PaddleOCR 异步解析（兼容已有事件循环）"""
        from src.paddleocr_client import PaddleOCRClient

        client = PaddleOCRClient()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run,
                    client.parse_images_async(image_paths, save_output=True)
                ).result()
        else:
            return asyncio.run(
                client.parse_images_async(image_paths, save_output=True)
            )

    def _simplify_results(self, ocr_results: list[dict]) -> list[dict]:
        """简化 OCR 结果，只保留 agent 分割所需的字段"""
        simplified = []
        page_index = 0
        for result in ocr_results:
            if "layoutParsingResults" not in result:
                continue
            for page in result["layoutParsingResults"]:
                if "prunedResult" not in page:
                    continue
                parsing_res = page["prunedResult"].get("parsing_res_list", [])
                slim_blocks = []
                for b in parsing_res:
                    content = b.get("block_content", "")
                    # 图片 block 的 content 始终为空，用 bbox 构造图片路径
                    if b.get("block_label") == "image" and not content:
                        bbox = b.get("block_bbox")
                        if bbox:
                            content = f"/images/img_in_image_box_{int(bbox[0])}_{int(bbox[1])}_{int(bbox[2])}_{int(bbox[3])}.jpg"
                    slim_blocks.append({
                        "block_label": b.get("block_label"),
                        "block_content": content,
                        "block_order": b.get("block_order"),
                    })
                simplified.append({
                    "page_index": page_index,
                    "blocks": slim_blocks,
                })
                page_index += 1
        return simplified

"""
OCR 中间件纯函数的单元测试

覆盖函数：
- OCRMiddleware._extract_image_paths
- OCRMiddleware._simplify_results
- OCRMiddleware.before_agent (Mocked)
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from langchain.messages import HumanMessage
from error_correction_agent.middleware.ocr_middleware import OCRMiddleware


@pytest.fixture
def middleware():
    return OCRMiddleware()


# ═══════════════════════════════════════════════════════════
# _extract_image_paths
# ═══════════════════════════════════════════════════════════


class TestExtractImagePaths:
    """_extract_image_paths 测试"""

    def test_valid_json_list(self, middleware):
        content = '["path/to/img1.png", "path/to/img2.png"]'
        result = middleware._extract_image_paths(content)
        assert result == ["path/to/img1.png", "path/to/img2.png"]

    def test_empty_list(self, middleware):
        assert middleware._extract_image_paths("[]") == []

    def test_invalid_json(self, middleware):
        assert middleware._extract_image_paths("not json") == []

    def test_non_list_json(self, middleware):
        """JSON 对象（非列表）应返回空"""
        assert middleware._extract_image_paths('{"key": "value"}') == []

    def test_list_with_non_strings(self, middleware):
        """列表元素不全是字符串应返回空"""
        assert middleware._extract_image_paths('[1, 2, 3]') == []

    def test_mixed_types(self, middleware):
        assert middleware._extract_image_paths('["a", 1]') == []

    def test_plain_text(self, middleware):
        assert middleware._extract_image_paths("请分析以下图片") == []

    def test_empty_string(self, middleware):
        assert middleware._extract_image_paths("") == []

    def test_single_path(self, middleware):
        result = middleware._extract_image_paths('["single.png"]')
        assert result == ["single.png"]


# ═══════════════════════════════════════════════════════════
# _simplify_results (与 workflow._simplify_ocr_results 逻辑一致)
# ═══════════════════════════════════════════════════════════


class TestSimplifyResults:
    """_simplify_results 测试"""

    def test_empty(self, middleware):
        assert middleware._simplify_results([]) == []

    def test_text_block(self, middleware):
        ocr = [{
            "layoutParsingResults": [{
                "prunedResult": {
                    "parsing_res_list": [{
                        "block_label": "text",
                        "block_content": "Hello",
                        "block_order": 1,
                    }]
                }
            }]
        }]
        result = middleware._simplify_results(ocr)
        assert len(result) == 1
        assert result[0]["blocks"][0]["block_content"] == "Hello"

    def test_chart_block_path(self, middleware):
        """chart 类型应生成 img_in_chart_box 路径"""
        ocr = [{
            "layoutParsingResults": [{
                "prunedResult": {
                    "parsing_res_list": [{
                        "block_label": "chart",
                        "block_content": "",
                        "block_order": 1,
                        "block_bbox": [10, 20, 30, 40],
                    }]
                }
            }]
        }]
        result = middleware._simplify_results(ocr)
        assert result[0]["blocks"][0]["block_content"] == "/images/img_in_chart_box_10_20_30_40.jpg"

    def test_image_block_path(self, middleware):
        """image 类型应生成 img_in_image_box 路径"""
        ocr = [{
            "layoutParsingResults": [{
                "prunedResult": {
                    "parsing_res_list": [{
                        "block_label": "image",
                        "block_content": "",
                        "block_order": 1,
                        "block_bbox": [100, 200, 300, 400],
                    }]
                }
            }]
        }]
        result = middleware._simplify_results(ocr)
        assert result[0]["blocks"][0]["block_content"] == "/images/img_in_image_box_100_200_300_400.jpg"

    def test_skip_missing_layout(self, middleware):
        assert middleware._simplify_results([{"other": 1}]) == []


# ═══════════════════════════════════════════════════════════
# before_agent
# ═══════════════════════════════════════════════════════════


class TestBeforeAgent:
    """before_agent 测试"""

    def test_no_messages(self, middleware):
        """无消息直接返回 None"""
        state = {"messages": []}
        assert middleware.before_agent(state, None) is None

    def test_no_image_paths(self, middleware):
        """无图片路径直接返回 None"""
        msg = HumanMessage(content="Hello")
        state = {"messages": [msg]}
        assert middleware.before_agent(state, None) is None

    def test_normal_flow(self, middleware, tmp_path):
        """正常流程：提取图片 -> OCR -> 注入结果"""
        # Mock _run_ocr
        with patch.object(middleware, "_run_ocr") as mock_run_ocr:
            mock_run_ocr.return_value = [{
                "layoutParsingResults": [{
                    "prunedResult": {
                        "parsing_res_list": [{
                            "block_label": "text",
                            "block_content": "OCR Result",
                            "block_order": 1,
                        }]
                    }
                }]
            }]

            # 构造 state
            msg = HumanMessage(content='["image.png"]')
            state = {"messages": [msg]}

            # Mock RESULTS_DIR，确保 agent_input.json 写入临时目录
            with patch("error_correction_agent.middleware.ocr_middleware.RESULTS_DIR", str(tmp_path)):
                result = middleware.before_agent(state, None)

            # 验证结果
            assert result is not None
            messages = result["messages"]
            # 这里的逻辑是替换了最后一条消息，所以长度应该不变（如果是1条输入，变成1条输出）
            # 但是 before_agent 返回的是 {"messages": new_messages}
            # 代码中: new_messages = messages[:-1] + [ocr_message]
            assert len(messages) == 1
            assert "OCR 解析完成" in messages[0].content
            assert "OCR Result" in messages[0].content

            # 验证 agent_input.json 是否生成
            assert (tmp_path / "agent_input.json").exists()

    def test_ocr_failure(self, middleware):
        """OCR 失败应返回错误提示消息"""
        with patch.object(middleware, "_run_ocr") as mock_run_ocr:
            mock_run_ocr.side_effect = Exception("API Error")

            msg = HumanMessage(content='["image.png"]')
            state = {"messages": [msg]}

            result = middleware.before_agent(state, None)

            assert result is not None
            messages = result["messages"]
            # 失败时: return {"messages": messages + [error_msg]}
            assert len(messages) == 2
            assert "OCR 解析失败" in messages[-1].content

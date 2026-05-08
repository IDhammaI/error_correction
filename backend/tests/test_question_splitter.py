from src.question_splitter import build_questions_from_ocr
from src.question_splitter.coordinate_mapper import TRUST_HIGH, TRUST_LOW


def _region(x1, y1, x2, y2):
    return {
        "qus_location": {
            "points": [
                {"x": x1, "y": y1},
                {"x": x2, "y": y1},
                {"x": x2, "y": y2},
                {"x": x1, "y": y2},
            ]
        }
    }


def test_build_questions_uses_baidu_regions_and_paddleocr_content():
    ocr_data = [
        {
            "page_index": 0,
            "blocks": [
                {
                    "block_label": "paragraph_title",
                    "block_content": "一、选择题",
                    "block_order": 1,
                    "block_bbox": [0, 0, 500, 30],
                },
                {
                    "block_label": "text",
                    "block_content": "1. 计算 1+1=()\nA. 1\nB. 2",
                    "block_order": 2,
                    "block_bbox": [10, 40, 480, 120],
                },
                {
                    "block_label": "text",
                    "block_content": "2. 写出公式含义。",
                    "block_order": 3,
                    "block_bbox": [10, 140, 480, 190],
                },
                {
                    "block_label": "formula",
                    "block_content": "$E=mc^2$",
                    "block_order": 4,
                    "block_bbox": [20, 195, 300, 240],
                },
                {
                    "block_label": "image",
                    "block_content": "/images/diagram.jpg",
                    "block_order": 5,
                    "block_bbox": [20, 245, 300, 340],
                },
            ],
        }
    ]
    baidu_pages = [
        {
            "page_index": 0,
            "result": {"qus_result": [_region(0, 35, 500, 130), _region(0, 130, 500, 360)]},
        }
    ]

    questions, debug, warnings = build_questions_from_ocr(ocr_data, baidu_pages, subject="数学")

    assert warnings == []
    assert debug["region_count"] == 2
    assert [q["question_id"] for q in questions] == ["1", "2"]
    assert questions[0]["section_title"] == "一、选择题"
    assert questions[0]["question_type"] == "选择题"
    assert questions[0]["options"] == ["A. 1", "B. 2"]
    assert questions[1]["has_formula"] is True
    assert questions[1]["has_image"] is True
    assert questions[1]["image_refs"] == ["/images/diagram.jpg"]
    assert questions[1]["source_regions"] == [{"page_index": 0, "region_index": 1}]


def test_build_questions_falls_back_to_ocr_markers_without_regions():
    ocr_data = [
        {
            "page_index": 0,
            "blocks": [
                {
                    "block_label": "text",
                    "block_content": "1. 第一题\n2. 第二题",
                    "block_order": 1,
                    "block_bbox": [10, 10, 500, 100],
                }
            ],
        }
    ]

    questions, debug, warnings = build_questions_from_ocr(ocr_data, [], subject="数学")

    assert [q["question_id"] for q in questions] == ["1", "2"]
    assert debug["region_count"] == 0
    assert warnings[0].startswith("BAIDU_PAPER_CUT_NO_REGIONS")


def test_build_questions_can_split_by_region_when_number_missing():
    ocr_data = [
        {
            "page_index": 0,
            "blocks": [
                {
                    "block_label": "text",
                    "block_content": "已知 x=1，求 x+1。",
                    "block_order": 1,
                    "block_bbox": [10, 10, 500, 80],
                },
                {
                    "block_label": "text",
                    "block_content": "若 y=2，求 y+2。",
                    "block_order": 2,
                    "block_bbox": [10, 120, 500, 180],
                },
            ],
        }
    ]
    baidu_pages = [
        {
            "page_index": 0,
            "result": {"qus_result": [_region(0, 0, 520, 100), _region(0, 100, 520, 210)]},
        }
    ]

    questions, debug, warnings = build_questions_from_ocr(ocr_data, baidu_pages)

    assert warnings == []
    assert debug["region_count"] == 2
    assert len(questions) == 2
    assert questions[0]["question_id"] == "1"
    assert questions[1]["question_id"] == "2"


def test_build_questions_assigns_regions_after_coordinate_normalization():
    ocr_data = [
        {
            "page_index": 0,
            "page_width": 1000,
            "page_height": 1000,
            "blocks": [
                {
                    "block_label": "text",
                    "block_content": "Known x=1.",
                    "block_order": 1,
                    "block_bbox": [100, 100, 400, 300],
                }
            ],
        }
    ]
    baidu_pages = [
        {
            "page_index": 0,
            "result": {"qus_result": [_region(50, 50, 200, 150)]},
        }
    ]
    page_sources = [
        {
            "page_index": 0,
            "ocr_page_width": 1000,
            "ocr_page_height": 1000,
            "baidu_image_width": 500,
            "baidu_image_height": 500,
            "coordinate_trust": TRUST_HIGH,
        }
    ]

    questions, debug, warnings = build_questions_from_ocr(
        ocr_data,
        baidu_pages,
        page_image_sources=page_sources,
    )

    assert warnings == []
    assert questions[0]["source_regions"] == [{"page_index": 0, "region_index": 0}]
    assert debug["assignments"][0]["coordinate_trust"] == TRUST_HIGH


def test_build_questions_ignores_regions_when_coordinate_trust_is_low():
    ocr_data = [
        {
            "page_index": 0,
            "page_width": 1000,
            "page_height": 1000,
            "blocks": [
                {
                    "block_label": "text",
                    "block_content": "Known x=1.",
                    "block_order": 1,
                    "block_bbox": [100, 100, 400, 300],
                },
                {
                    "block_label": "text",
                    "block_content": "Known y=2.",
                    "block_order": 2,
                    "block_bbox": [100, 500, 400, 700],
                },
            ],
        }
    ]
    baidu_pages = [
        {
            "page_index": 0,
            "result": {"qus_result": [_region(0, 0, 500, 250), _region(0, 250, 500, 500)]},
        }
    ]
    page_sources = [
        {
            "page_index": 0,
            "ocr_page_width": 1000,
            "ocr_page_height": 1000,
            "baidu_image_width": 500,
            "baidu_image_height": 500,
            "coordinate_trust": TRUST_LOW,
        }
    ]

    questions, debug, warnings = build_questions_from_ocr(
        ocr_data,
        baidu_pages,
        page_image_sources=page_sources,
    )

    assert warnings == []
    assert len(questions) == 1
    assert questions[0]["source_regions"] == []
    assert [item["region_key"] for item in debug["assignments"]] == [None, None]

from src.question_splitter.coordinate_mapper import (
    TRUST_HIGH,
    TRUST_LOW,
    TRUST_MEDIUM,
    apply_coordinate_mapping,
    compute_coordinate_trust,
    normalize_bbox_to_page,
)


def test_normalize_bbox_to_page_clamps_values():
    assert normalize_bbox_to_page([-10, 20, 210, 420], 200, 400) == (
        0.0,
        0.05,
        1.0,
        1.0,
    )


def test_compute_coordinate_trust_uses_aspect_ratio_and_geometry_flags():
    assert compute_coordinate_trust(
        ocr_width=1000,
        ocr_height=2000,
        image_width=500,
        image_height=1000,
    ) == TRUST_HIGH

    assert compute_coordinate_trust(
        ocr_width=1000,
        ocr_height=2000,
        image_width=530,
        image_height=1000,
    ) == TRUST_MEDIUM

    assert compute_coordinate_trust(
        ocr_width=1000,
        ocr_height=2000,
        image_width=1000,
        image_height=1000,
    ) == TRUST_LOW

    assert compute_coordinate_trust(
        ocr_width=1000,
        ocr_height=2000,
        image_width=500,
        image_height=1000,
        ocr_credentials={"use_doc_orientation": True},
    ) == TRUST_MEDIUM


def test_apply_coordinate_mapping_adds_normalized_bboxes_for_ocr_and_baidu():
    ocr_data = [
        {
            "page_index": 0,
            "page_width": 1000,
            "page_height": 2000,
            "blocks": [{"block_bbox": [100, 200, 500, 600]}],
        }
    ]
    baidu_pages = [
        {
            "page_index": 0,
            "result": {
                "qus_result": [
                    {
                        "qus_location": {
                            "points": [
                                {"x": 50, "y": 100},
                                {"x": 250, "y": 100},
                                {"x": 250, "y": 300},
                                {"x": 50, "y": 300},
                            ]
                        }
                    }
                ]
            },
        }
    ]
    page_sources = [
        {
            "page_index": 0,
            "ocr_page_width": 1000,
            "ocr_page_height": 2000,
            "baidu_image_width": 500,
            "baidu_image_height": 1000,
            "coordinate_trust": TRUST_HIGH,
        }
    ]

    mapped_ocr, mapped_baidu, debug = apply_coordinate_mapping(
        ocr_data,
        baidu_pages,
        page_sources,
    )

    assert mapped_ocr[0]["blocks"][0]["normalized_bbox"] == [0.1, 0.1, 0.5, 0.3]
    question = mapped_baidu[0]["result"]["qus_result"][0]
    assert question["normalized_bbox"] == [0.1, 0.1, 0.5, 0.3]
    assert debug["pages"][0]["coordinate_trust"] == TRUST_HIGH

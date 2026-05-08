import shutil
from pathlib import Path

from src.question_splitter import page_images
from src.question_splitter.coordinate_mapper import TRUST_HIGH, TRUST_LOW


def _work_dir(name):
    root = Path(__file__).resolve().parents[1] / "runtime_data" / "test_page_images" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _raw_page(width=1000, height=2000, output_images=None):
    page = {
        "prunedResult": {
            "width": width,
            "height": height,
            "parsing_res_list": [],
        }
    }
    if output_images is not None:
        page["outputImages"] = output_images
    return page


def test_extract_page_image_sources_uses_saved_pdf_input_image(monkeypatch):
    work_dir = _work_dir("pdf_input_image")
    pdf_path = str(work_dir / "paper.pdf")
    Path(pdf_path).write_bytes(b"%PDF")
    rendered = work_dir / "input_image_paper_0.jpg"
    rendered.write_bytes(b"jpg")
    raw_results = [
        {
            "layoutParsingResults": [
                _raw_page(output_images={"page": "https://example.test/page.jpg"})
            ]
        }
    ]
    monkeypatch.setattr(page_images, "get_image_size", lambda path: (1000, 2000))

    sources, warnings = page_images.extract_page_image_sources(
        raw_results,
        [pdf_path],
        output_dir=str(work_dir),
    )

    assert warnings == []
    assert sources[0]["source_type"] == "pdf"
    assert sources[0]["baidu_image_path"] == str(rendered)
    assert sources[0]["coordinate_trust"] == TRUST_HIGH


def test_extract_page_image_sources_warns_when_pdf_page_image_missing():
    work_dir = _work_dir("missing_pdf_output_image")
    raw_results = [{"layoutParsingResults": [_raw_page()]}]
    sources, warnings = page_images.extract_page_image_sources(
        raw_results,
        [str(work_dir / "missing.pdf")],
        output_dir=str(work_dir),
    )

    assert warnings == ["BAIDU_PAPER_CUT_PAGE_IMAGE_MISSING: page_index=0"]
    assert sources[0]["baidu_image_path"] is None
    assert sources[0]["coordinate_trust"] == TRUST_LOW


def test_extract_page_image_sources_does_not_use_layout_visualization():
    work_dir = _work_dir("layout_visualization_not_input")
    pdf_path = str(work_dir / "paper.pdf")
    Path(pdf_path).write_bytes(b"%PDF")
    layout_vis = work_dir / "layout_det_res_paper_0.jpg"
    layout_vis.write_bytes(b"jpg")
    raw_results = [
        {
            "layoutParsingResults": [
                _raw_page(output_images={"layout_det_res": "https://example.test/page.jpg"})
            ]
        }
    ]

    sources, warnings = page_images.extract_page_image_sources(
        raw_results,
        [pdf_path],
        output_dir=str(work_dir),
    )

    assert warnings == ["BAIDU_PAPER_CUT_PAGE_IMAGE_MISSING: page_index=0"]
    assert sources[0]["baidu_image_path"] is None


def test_extract_page_image_sources_uses_original_image_for_image_input(monkeypatch):
    work_dir = _work_dir("image_input")
    image_path = work_dir / "page.png"
    image_path.write_bytes(b"png")
    raw_results = [{"layoutParsingResults": [_raw_page(width=800, height=600)]}]
    monkeypatch.setattr(page_images, "get_image_size", lambda path: (800, 600))

    sources, warnings = page_images.extract_page_image_sources(
        raw_results,
        [str(image_path)],
        output_dir=str(work_dir),
    )

    assert warnings == []
    assert sources[0]["source_type"] == "image"
    assert sources[0]["baidu_image_path"] == str(image_path)
    assert sources[0]["coordinate_trust"] == TRUST_HIGH


def test_extract_page_image_sources_fills_missing_ocr_size(monkeypatch):
    work_dir = _work_dir("missing_ocr_size")
    image_path = work_dir / "page.png"
    image_path.write_bytes(b"png")
    raw_results = [
        {
            "layoutParsingResults": [
                {"prunedResult": {"parsing_res_list": []}}
            ]
        }
    ]
    monkeypatch.setattr(page_images, "get_image_size", lambda path: (800, 600))

    sources, warnings = page_images.extract_page_image_sources(
        raw_results,
        [str(image_path)],
        output_dir=str(work_dir),
    )

    assert warnings == []
    assert sources[0]["ocr_page_width"] == 800
    assert sources[0]["ocr_page_height"] == 600
    assert sources[0]["coordinate_trust"] == TRUST_HIGH


def test_discover_page_image_sources_matches_cached_pdf_first_ocr_order(monkeypatch):
    work_dir = _work_dir("cached_mixed_order")
    image_path = work_dir / "upload.png"
    image_path.write_bytes(b"png")
    pdf_path = work_dir / "paper.pdf"
    pdf_path.write_bytes(b"%PDF")
    rendered = work_dir / "input_image_paper_0.jpg"
    rendered.write_bytes(b"jpg")
    ocr_data = [
        {"page_index": 0, "page_width": 1000, "page_height": 2000, "blocks": []},
        {"page_index": 1, "page_width": 800, "page_height": 600, "blocks": []},
    ]
    monkeypatch.setattr(
        page_images,
        "get_image_size",
        lambda path: (1000, 2000) if str(path).endswith(".jpg") else (800, 600),
    )

    sources, warnings = page_images.discover_page_image_sources_from_ocr_data(
        ocr_data,
        [str(image_path), str(pdf_path)],
        output_dir=str(work_dir),
    )

    assert warnings == []
    assert sources[0]["source_type"] == "pdf"
    assert sources[0]["baidu_image_path"] == str(rendered)
    assert sources[1]["source_type"] == "image"
    assert sources[1]["baidu_image_path"] == str(image_path)


def test_discover_page_image_sources_fills_missing_cached_ocr_size(monkeypatch):
    work_dir = _work_dir("cached_missing_ocr_size")
    image_path = work_dir / "upload.png"
    image_path.write_bytes(b"png")
    ocr_data = [{"page_index": 0, "blocks": []}]
    monkeypatch.setattr(page_images, "get_image_size", lambda path: (800, 600))

    sources, warnings = page_images.discover_page_image_sources_from_ocr_data(
        ocr_data,
        [str(image_path)],
        output_dir=str(work_dir),
    )

    assert warnings == []
    assert sources[0]["ocr_page_width"] == 800
    assert sources[0]["ocr_page_height"] == 600
    assert sources[0]["coordinate_trust"] == TRUST_HIGH

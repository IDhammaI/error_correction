import pytest

from src.baidu_paper_cut_client import (
    BaiduPaperCutClient,
    BaiduPaperCutError,
    cut_images_concurrently,
)


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text="{}"):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


def test_requires_api_key():
    with pytest.raises(BaiduPaperCutError) as exc:
        BaiduPaperCutClient(api_key="")
    assert exc.value.code == "BAIDU_PAPER_CUT_NOT_CONFIGURED"


def test_posts_base64_payload_and_bearer_header(monkeypatch):
    captured = {}

    def fake_post(url, headers, data, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        return DummyResponse(payload={"qus_result_num": 0, "qus_result": []})

    monkeypatch.setattr("src.baidu_paper_cut_client.requests.post", fake_post)
    monkeypatch.setattr(
        BaiduPaperCutClient,
        "_image_to_base64",
        staticmethod(lambda path: "ZmFrZS1pbWFnZQ=="),
    )
    client = BaiduPaperCutClient(api_url="https://example.test/cut", api_key="bce-v3/test")

    result = client.cut_image("page.jpg")

    assert result["qus_result"] == []
    assert captured["url"] == "https://example.test/cut"
    assert captured["headers"]["Authorization"] == "Bearer bce-v3/test"
    assert captured["data"]["image"] == "ZmFrZS1pbWFnZQ=="
    assert captured["data"]["language_type"] == "CHN_ENG"
    assert captured["data"]["words_type"] == "handprint_mix"


def test_maps_auth_failure_without_exposing_key(monkeypatch):
    def fake_post(*args, **kwargs):
        return DummyResponse(status_code=401, text="unauthorized")

    monkeypatch.setattr("src.baidu_paper_cut_client.requests.post", fake_post)
    monkeypatch.setattr(
        BaiduPaperCutClient,
        "_image_to_base64",
        staticmethod(lambda path: "base64"),
    )
    client = BaiduPaperCutClient(api_key="secret-token")

    with pytest.raises(BaiduPaperCutError) as exc:
        client.cut_image("page.jpg")

    assert exc.value.code == "BAIDU_PAPER_CUT_AUTH_FAILED"
    assert "secret-token" not in str(exc.value)


def test_retries_json_rate_limit_then_succeeds(monkeypatch):
    calls = []
    sleeps = []

    def fake_post(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return DummyResponse(
                payload={
                    "error_code": 18,
                    "error_msg": "Open api qps request limit reached",
                },
            )
        return DummyResponse(payload={"qus_result_num": 0, "qus_result": []})

    monkeypatch.setattr("src.baidu_paper_cut_client.requests.post", fake_post)
    monkeypatch.setattr("src.baidu_paper_cut_client.time.sleep", sleeps.append)
    monkeypatch.setattr(
        BaiduPaperCutClient,
        "_image_to_base64",
        staticmethod(lambda path: "base64"),
    )
    client = BaiduPaperCutClient(api_key="token", max_retries=2)

    result = client.cut_image("page.jpg")

    assert result["qus_result"] == []
    assert len(calls) == 2
    assert sleeps == [1.0]


def test_raises_rate_limited_after_json_retries(monkeypatch):
    calls = []
    sleeps = []

    def fake_post(*args, **kwargs):
        calls.append(1)
        return DummyResponse(
            payload={
                "error_code": 18,
                "error_msg": "Open api qps request limit reached",
            },
        )

    monkeypatch.setattr("src.baidu_paper_cut_client.requests.post", fake_post)
    monkeypatch.setattr("src.baidu_paper_cut_client.time.sleep", sleeps.append)
    monkeypatch.setattr(
        BaiduPaperCutClient,
        "_image_to_base64",
        staticmethod(lambda path: "base64"),
    )
    client = BaiduPaperCutClient(api_key="token", max_retries=2)

    with pytest.raises(BaiduPaperCutError) as exc:
        client.cut_image("page.jpg")

    assert exc.value.code == "BAIDU_PAPER_CUT_RATE_LIMITED"
    assert len(calls) == 2
    assert sleeps == [1.0]


def test_cut_images_concurrently_preserves_page_order(monkeypatch):
    paths = [f"page-{idx}.jpg" for idx in range(3)]

    def fake_cut_image(path):
        return {"path": path}

    client = BaiduPaperCutClient(api_key="token")
    monkeypatch.setattr(client, "cut_image", fake_cut_image)

    results = cut_images_concurrently(client, paths, max_workers=3)

    assert [item["page_index"] for item in results] == [0, 1, 2]
    assert [item["result"]["path"] for item in results] == paths

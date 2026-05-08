"""Client for Baidu paper_cut_edu question-boundary OCR API."""

from __future__ import annotations

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


DEFAULT_PAPER_CUT_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/paper_cut_edu"
RATE_LIMIT_ERROR_CODES = {"17", "18", "19"}
AUTH_ERROR_CODES = {"110", "111", "216100", "216101"}


class BaiduPaperCutError(RuntimeError):
    """Raised when Baidu paper_cut_edu cannot return a usable response."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.response_text = response_text


class BaiduPaperCutClient:
    """Small synchronous client for Baidu's education paper cutting API."""

    def __init__(
        self,
        *,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: tuple[int, int] = (10, 60),
        max_retries: int = 3,
    ) -> None:
        self.api_url = api_url or DEFAULT_PAPER_CUT_URL
        self.api_key = api_key or ""
        self.timeout = timeout
        self.max_retries = max(1, int(max_retries))
        if not self.api_key:
            raise BaiduPaperCutError(
                "BAIDU_PAPER_CUT_NOT_CONFIGURED",
                "Baidu paper_cut_edu API key is not configured.",
            )

    @property
    def _authorization(self) -> str:
        token = self.api_key.strip()
        if token.lower().startswith("bearer "):
            return token
        return f"Bearer {token}"

    @property
    def _request_kwargs(self) -> Dict[str, Any]:
        from core.config import settings

        kwargs: Dict[str, Any] = {"timeout": self.timeout}
        if not settings.trust_env:
            kwargs["proxies"] = {"http": None, "https": None}
        return kwargs

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": self._authorization,
        }

    @staticmethod
    def _retry_delay(attempt: int, response: Optional[requests.Response] = None) -> float:
        retry_after = (getattr(response, "headers", {}) or {}).get("Retry-After")
        if retry_after:
            try:
                return min(30.0, max(0.0, float(retry_after)))
            except ValueError:
                pass
        return min(30.0, float(attempt))

    @staticmethod
    def _image_to_base64(image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def cut_image(
        self,
        image_path: str,
        *,
        language_type: str = "CHN_ENG",
        detect_direction: bool = False,
        words_type: str = "handprint_mix",
        splice_text: bool = False,
        enhance: bool = False,
        only_split: bool = False,
    ) -> Dict[str, Any]:
        """Return raw Baidu API JSON for one image."""

        payload = {
            "image": self._image_to_base64(image_path),
            "language_type": language_type,
            "detect_direction": str(bool(detect_direction)).lower(),
            "words_type": words_type,
            "splice_text": str(bool(splice_text)).lower(),
            "enhance": str(bool(enhance)).lower(),
            "only_split": str(bool(only_split)).lower(),
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self._headers(),
                    data=payload,
                    **self._request_kwargs,
                )
            except requests.Timeout as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise BaiduPaperCutError(
                        "BAIDU_PAPER_CUT_TIMEOUT",
                        "Baidu paper_cut_edu request timed out.",
                    ) from exc
                time.sleep(self._retry_delay(attempt))
                continue
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise BaiduPaperCutError(
                        "BAIDU_PAPER_CUT_REQUEST_FAILED",
                        "Baidu paper_cut_edu request failed.",
                    ) from exc
                time.sleep(self._retry_delay(attempt))
                continue

            if response.status_code in (401, 403):
                raise BaiduPaperCutError(
                    "BAIDU_PAPER_CUT_AUTH_FAILED",
                    "Baidu paper_cut_edu authentication failed.",
                    status_code=response.status_code,
                    response_text=response.text[:500],
                )
            if response.status_code == 429:
                if attempt >= self.max_retries:
                    raise BaiduPaperCutError(
                        "BAIDU_PAPER_CUT_RATE_LIMITED",
                        "Baidu paper_cut_edu request was rate limited.",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )
                time.sleep(self._retry_delay(attempt, response))
                continue
            if response.status_code >= 500:
                if attempt >= self.max_retries:
                    raise BaiduPaperCutError(
                        "BAIDU_PAPER_CUT_SERVER_ERROR",
                        "Baidu paper_cut_edu service returned a server error.",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )
                time.sleep(self._retry_delay(attempt, response))
                continue
            if response.status_code != 200:
                raise BaiduPaperCutError(
                    "BAIDU_PAPER_CUT_HTTP_ERROR",
                    f"Baidu paper_cut_edu returned HTTP {response.status_code}.",
                    status_code=response.status_code,
                    response_text=response.text[:500],
                )

            try:
                result = response.json()
            except json.JSONDecodeError as exc:
                raise BaiduPaperCutError(
                    "BAIDU_PAPER_CUT_INVALID_JSON",
                    "Baidu paper_cut_edu returned invalid JSON.",
                    response_text=response.text[:500],
                ) from exc

            if isinstance(result, dict) and result.get("error_code"):
                code = str(result.get("error_code"))
                if code in AUTH_ERROR_CODES:
                    mapped = "BAIDU_PAPER_CUT_AUTH_FAILED"
                elif code in RATE_LIMIT_ERROR_CODES:
                    if attempt < self.max_retries:
                        time.sleep(self._retry_delay(attempt, response))
                        continue
                    mapped = "BAIDU_PAPER_CUT_RATE_LIMITED"
                else:
                    mapped = "BAIDU_PAPER_CUT_API_ERROR"
                raise BaiduPaperCutError(
                    mapped,
                    str(result.get("error_msg") or "Baidu paper_cut_edu API error."),
                    response_text=json.dumps(result, ensure_ascii=False)[:500],
                )

            if not isinstance(result, dict):
                raise BaiduPaperCutError(
                    "BAIDU_PAPER_CUT_INVALID_RESPONSE",
                    "Baidu paper_cut_edu returned a non-object response.",
                )
            return result

        raise BaiduPaperCutError(
            "BAIDU_PAPER_CUT_REQUEST_FAILED",
            "Baidu paper_cut_edu request failed.",
        ) from last_error


def cut_images_concurrently(
    client: BaiduPaperCutClient,
    image_paths: Iterable[str],
    *,
    max_workers: int = 3,
) -> List[Dict[str, Any]]:
    """Cut image pages concurrently and return results aligned by page index."""

    paths = list(image_paths)
    if not paths:
        return []

    worker_count = max(1, min(int(max_workers), len(paths)))
    page_results: List[Optional[Dict[str, Any]]] = [None] * len(paths)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(client.cut_image, path): (idx, path)
            for idx, path in enumerate(paths)
        }
        for future in as_completed(futures):
            idx, path = futures[future]
            page_results[idx] = {
                "page_index": idx,
                "image_path": str(Path(path)),
                "result": future.result(),
            }

    return [item for item in page_results if item is not None]

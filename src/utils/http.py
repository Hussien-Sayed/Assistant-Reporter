from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import requests


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5


class HttpError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.response_text = response_text


def _sleep_backoff(base_delay_seconds: float, attempt_index: int) -> None:
    time.sleep(base_delay_seconds * (2**attempt_index))


def request(
    method: str,
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 20.0,
    retry: RetryConfig | None = None,
) -> requests.Response:
    retry = retry or RetryConfig()

    merged_headers: dict[str, str] = {"User-Agent": "NewsReporter/1.0"}
    if headers:
        merged_headers.update(dict(headers))

    last_exc: Optional[Exception] = None

    for attempt in range(retry.max_attempts):
        try:
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                headers=merged_headers,
                timeout=timeout_seconds,
            )

            if 200 <= resp.status_code < 300:
                return resp

            if 500 <= resp.status_code < 600 and attempt < retry.max_attempts - 1:
                _sleep_backoff(retry.base_delay_seconds, attempt)
                continue

            raise HttpError(
                f"HTTP {resp.status_code} error for {url}",
                url=url,
                status_code=resp.status_code,
                response_text=resp.text,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retry.max_attempts - 1:
                _sleep_backoff(retry.base_delay_seconds, attempt)
                continue
            raise HttpError(f"Request failed for {url}: {exc}", url=url) from exc

    raise HttpError(f"Request failed for {url}", url=url) from last_exc


def get_json(
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 20.0,
    retry: RetryConfig | None = None,
) -> Any:
    resp = request(
        "GET",
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry=retry,
    )
    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        raise HttpError(
            f"Invalid JSON response from {url}",
            url=url,
            status_code=resp.status_code,
            response_text=resp.text,
        ) from exc


def post_json(
    url: str,
    *,
    json_body: Mapping[str, Any],
    headers: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 20.0,
    retry: RetryConfig | None = None,
) -> Any:
    resp = request(
        "POST",
        url,
        json_body=json_body,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry=retry,
    )
    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        raise HttpError(
            f"Invalid JSON response from {url}",
            url=url,
            status_code=resp.status_code,
            response_text=resp.text,
        ) from exc


def get_text(
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout_seconds: float = 20.0,
    retry: RetryConfig | None = None,
) -> str:
    resp = request(
        "GET",
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        retry=retry,
    )
    return resp.text

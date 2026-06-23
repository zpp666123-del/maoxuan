from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

import httpx


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


class ImageGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model: str
    base_url: str
    temperature: float

    @classmethod
    def from_env(cls) -> "LLMSettings":
        overrides = runtime_llm_settings.current()
        api_key = overrides.api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = overrides.model or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL")
        base_url = (overrides.base_url or os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        temperature = overrides.temperature

        missing = []
        if not api_key:
            missing.append("API key")
        if not model:
            missing.append("model")
        if missing:
            raise LLMConfigurationError("Missing required LLM setting(s): " + ", ".join(missing))

        return cls(api_key=api_key, model=model, base_url=base_url, temperature=temperature)


@dataclass(frozen=True)
class ImageSettings:
    api_key: str
    model: str
    base_url: str
    size: str
    quality: str
    output_format: str

    @classmethod
    def from_env(cls) -> "ImageSettings":
        overrides = runtime_llm_settings.current()
        api_key = (
            overrides.api_key
            or os.getenv("IMAGE_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        model = overrides.image_model or os.getenv("IMAGE_MODEL") or "gpt-image-2"
        base_url = (
            overrides.image_base_url
            or overrides.base_url
            or os.getenv("IMAGE_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")

        if not api_key:
            raise LLMConfigurationError("Missing required image setting(s): API key")

        return cls(
            api_key=api_key,
            model=model,
            base_url=base_url,
            size=overrides.image_size,
            quality=overrides.image_quality,
            output_format=overrides.image_output_format,
        )


@dataclass(frozen=True)
class RuntimeLLMOverrides:
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.2
    image_model: str | None = None
    image_base_url: str | None = None
    image_size: str = "1024x1024"
    image_quality: str = "low"
    image_output_format: str = "png"


class RuntimeLLMSettings:
    def __init__(self) -> None:
        self._lock = Lock()
        self._overrides = RuntimeLLMOverrides()

    def current(self) -> RuntimeLLMOverrides:
        with self._lock:
            return self._overrides

    def update(
        self,
        *,
        api_key: str | None = None,
        clear_api_key: bool = False,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        image_model: str | None = None,
        image_base_url: str | None = None,
        image_size: str | None = None,
        image_quality: str | None = None,
        image_output_format: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._overrides
            next_api_key = current.api_key
            if clear_api_key:
                next_api_key = None
            elif api_key:
                next_api_key = api_key

            self._overrides = RuntimeLLMOverrides(
                api_key=next_api_key,
                model=model.strip() if model and model.strip() else current.model,
                base_url=base_url.rstrip("/") if base_url and base_url.strip() else current.base_url,
                temperature=temperature if temperature is not None else current.temperature,
                image_model=image_model.strip() if image_model and image_model.strip() else current.image_model,
                image_base_url=image_base_url.rstrip("/") if image_base_url and image_base_url.strip() else current.image_base_url,
                image_size=image_size.strip() if image_size and image_size.strip() else current.image_size,
                image_quality=image_quality.strip() if image_quality and image_quality.strip() else current.image_quality,
                image_output_format=(
                    image_output_format.strip() if image_output_format and image_output_format.strip() else current.image_output_format
                ),
            )
            return self._summary_unlocked()

    def summary(self) -> dict[str, Any]:
        with self._lock:
            return self._summary_unlocked()

    def _summary_unlocked(self) -> dict[str, Any]:
        overrides = self._overrides
        env_has_api_key = bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
        env_model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL")
        env_base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        env_image_model = os.getenv("IMAGE_MODEL")
        env_image_base_url = os.getenv("IMAGE_BASE_URL")
        return {
            "baseUrl": overrides.base_url or env_base_url or "https://api.openai.com/v1",
            "model": overrides.model or env_model or "",
            "hasApiKey": bool(overrides.api_key or env_has_api_key),
            "apiKeySource": "runtime" if overrides.api_key else ("environment" if env_has_api_key else "missing"),
            "temperature": overrides.temperature,
            "imageBaseUrl": overrides.image_base_url or env_image_base_url or overrides.base_url or env_base_url or "https://api.openai.com/v1",
            "imageModel": overrides.image_model or env_image_model or "gpt-image-2",
            "imageSize": overrides.image_size,
            "imageQuality": overrides.image_quality,
            "imageOutputFormat": overrides.image_output_format,
        }


runtime_llm_settings = RuntimeLLMSettings()


class OpenAICompatibleStreamClient:
    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    async def stream_chat(self, messages: list[dict[str, str]], temperature: float | None = None) -> AsyncIterator[str]:
        timeout = httpx.Timeout(90.0, connect=10.0, read=90.0, write=30.0, pool=10.0)
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature if temperature is None else temperature,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.settings.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode("utf-8", errors="replace")
                        raise LLMProviderError(f"LLM provider returned {response.status_code}: {body[:500]}")

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        raw = line.removeprefix("data:").strip()
                        if not raw or raw == "[DONE]":
                            continue
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError as exc:
                            raise LLMProviderError(f"Invalid streaming JSON from LLM provider: {raw[:200]}") from exc

                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        content = delta.get("content")
                        if content:
                            yield content
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"LLM provider request failed: {exc}") from exc


class OpenAICompatibleImageClient:
    def __init__(self, settings: ImageSettings | None = None) -> None:
        self.settings = settings or ImageSettings.from_env()

    async def generate_image(self, prompt: str) -> dict[str, Any]:
        timeout = httpx.Timeout(120.0, connect=10.0, read=120.0, write=30.0, pool=10.0)
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "prompt": prompt,
            "n": 1,
            "size": self.settings.size,
            "quality": self.settings.quality,
            "output_format": self.settings.output_format,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.settings.base_url}/images/generations",
                    headers=headers,
                    json=payload,
                )
                if response.status_code >= 400:
                    body = response.text
                    raise ImageGenerationError(f"Image provider returned {response.status_code}: {body[:500]}")
                data = response.json()
        except httpx.HTTPError as exc:
            raise ImageGenerationError(f"Image provider request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ImageGenerationError("Image provider returned invalid JSON") from exc

        images = data.get("data") or []
        if not images:
            raise ImageGenerationError("Image provider returned no image data")
        item = images[0]
        if item.get("b64_json"):
            return {
                "kind": "b64_json",
                "b64_json": item["b64_json"],
                "outputFormat": self.settings.output_format,
                "model": self.settings.model,
                "usage": data.get("usage"),
            }
        if item.get("url"):
            return {
                "kind": "url",
                "url": item["url"],
                "outputFormat": Path(str(item["url"]).split("?", 1)[0]).suffix.lstrip(".") or self.settings.output_format,
                "model": self.settings.model,
                "usage": data.get("usage"),
            }
        raise ImageGenerationError("Image provider response did not include b64_json or url")

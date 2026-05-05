from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import groq

from src.config.settings import Settings, SettingsError, get_settings


class VisionLlmApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImageDescription:
    description: str
    model: str


class VisionLlmClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        if settings is None:
            settings = get_settings()

        self.model_name = model_name or settings.vision_model
        self.api_key = api_key or settings.groq_api_key

        self.client: Optional[groq.Groq] = None
        if self.api_key:
            self.client = groq.Groq(api_key=self.api_key)

    def describe_image_url(
        self,
        image_url: str,
        *,
        prompt: str = "Describe this image.",
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> ImageDescription:
        if not image_url or not image_url.strip():
            return ImageDescription(description="", model=self.model_name)

        if not self.api_key or self.client is None:
            raise SettingsError("GROQ_API_KEY is required for VisionLlmClient")

        # Groq chat API is OpenAI-style; many models accept multimodal content.
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            temperature=float(temperature),
            max_completion_tokens=int(max_tokens),
            top_p=1,
            stream=False,
        )

        content = response.choices[0].message.content
        if not content:
            raise VisionLlmApiError("Vision LLM returned empty response")

        return ImageDescription(description=str(content).strip(), model=self.model_name)

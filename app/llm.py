import os
from typing import Optional


class LLMProvider:
    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Set GOOGLE_API_KEY or GEMINI_API_KEY before using Gemini")

        from google import genai

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return getattr(response, "text", None) or str(response)
        except Exception as exc:
            message = str(exc)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                raise RuntimeError(
                    "Gemini free-tier quota was exceeded. Please wait a bit or use a different API key/account."
                ) from exc
            raise


def get_llm_provider() -> LLMProvider:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Set GOOGLE_API_KEY or GEMINI_API_KEY before using Gemini")
    return GeminiProvider(api_key=api_key)

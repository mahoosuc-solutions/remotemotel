from __future__ import annotations

import os
import requests
from typing import Optional


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider returns an error response."""


class LLMClient:
    """Simple abstraction that supports OpenAI or a local Ollama instance."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        if self.provider == "ollama":
            return self._generate_with_ollama(prompt, system_prompt)
        if self.provider == "openai":
            return self._generate_with_openai(prompt, system_prompt, temperature)
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------
    def _generate_with_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt if not system_prompt else f"{system_prompt}\n\n{prompt}",
            "stream": False,
        }
        response = requests.post(
            f"{self.ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=60,
        )
        if response.status_code != 200:
            raise LLMProviderError(
                f"Ollama request failed: {response.status_code} {response.text}"
            )
        data = response.json()
        return data.get("response", "").strip()

    def _generate_with_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> str:
        if not self.openai_api_key:
            raise LLMProviderError("OPENAI_API_KEY is not set")

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if response.status_code != 200:
            raise LLMProviderError(
                f"OpenAI request failed: {response.status_code} {response.text}"
            )
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0]["message"]["content"].strip()

"""
FinPay Qwen Client — Ollama Backend
────────────────────────────────────
Communicates with a self-hosted Qwen model via Ollama's /api/chat endpoint.

All connection parameters are configurable through environment variables:
    OLLAMA_BASE_URL   – Ollama server address  (default: http://172.16.0.249:11434)
    OLLAMA_MODEL      – Model tag              (default: qwen3.5:9b)
    OLLAMA_TEMPERATURE – Generation temperature (default: 0.3)
    OLLAMA_NUM_CTX     – Context window size    (default: 8192)
    OLLAMA_NUM_PREDICT – Max tokens to generate (default: 1024)
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load env files: ai-agent/.env → client/.env → root .env (first match wins)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
load_dotenv(os.path.join(_current_dir, ".env"))
load_dotenv(os.path.join(_parent_dir, "client", ".env"))
load_dotenv(os.path.join(_parent_dir, ".env"))


class QwenClient:
    """Client for Ollama-hosted Qwen models.

    Uses the Ollama /api/chat JSON format with stream=false
    for synchronous-style request/response interaction.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        num_ctx: Optional[int] = None,
        num_predict: Optional[int] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL", "http://172.16.0.249:11434")
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
        self.temperature = temperature if temperature is not None else float(
            os.getenv("OLLAMA_TEMPERATURE", "0.3")
        )
        self.num_ctx = num_ctx if num_ctx is not None else int(
            os.getenv("OLLAMA_NUM_CTX", "8192")
        )
        self.num_predict = num_predict if num_predict is not None else int(
            os.getenv("OLLAMA_NUM_PREDICT", "1024")
        )

        self.chat_url = f"{self.base_url}/api/chat"

    # ── sync request ─────────────────────────────────────────

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Synchronous chat completion via Ollama /api/chat."""
        payload = self._build_payload(messages, tools)

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(self.chat_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    # ── async request ────────────────────────────────────────

    async def chat_completion_async(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Asynchronous chat completion via Ollama /api/chat."""
        payload = self._build_payload(messages, tools)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self.chat_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    # ── payload builder ──────────────────────────────────────

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Construct the Ollama /api/chat request body."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
            # Disable extended thinking — we want direct answers
            "think": False,
        }

        if tools:
            payload["tools"] = tools

        return payload

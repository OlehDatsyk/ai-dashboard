"""
ai_service.py
==============
Thin, well-typed wrapper around the OpenAI Responses API.

This module is the *only* place in the codebase that talks to OpenAI.
Isolating it here means the Flask routes stay dumb (parse request -> call
service -> serialize response) and the AI provider could be swapped out
later (e.g. Azure OpenAI, Anthropic) by rewriting this single file.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Generator, Iterable

from openai import OpenAI, OpenAIError

from analytics import analytics_engine, estimate_tokens
from config import AVAILABLE_MODELS, config

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the AI provider returns an error or is misconfigured."""


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class AIResponse:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    response_time_ms: int
    raw: dict[str, Any] | None = None


class AIService:
    """Wraps the OpenAI Responses API for chat, playground, and structured output use cases."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def is_configured(self) -> bool:
        return bool(config.openai_api_key) and not config.openai_api_key.startswith("sk-your")

    @property
    def client(self) -> OpenAI:
        if not self.is_configured:
            raise AIServiceError(
                "OPENAI_API_KEY is not configured. Add a valid key to your .env file to enable AI features."
            )
        if self._client is None:
            self._client = OpenAI(api_key=config.openai_api_key)
        return self._client

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_input(messages: Iterable[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Extract plain text from a Responses API result object."""
        text = getattr(response, "output_text", None)
        if text:
            return text
        # Fallback: walk the structured output blocks manually.
        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    chunks.append(value)
        return "".join(chunks)

    @staticmethod
    def _usage(response: Any) -> tuple[int, int]:
        usage = getattr(response, "usage", None)
        if usage is None:
            return 0, 0
        prompt = getattr(usage, "input_tokens", 0) or 0
        completion = getattr(usage, "output_tokens", 0) or 0
        return prompt, completion

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        category: str = "chat",
        json_mode: bool = False,
        record_analytics: bool = True,
    ) -> AIResponse:
        """Run a single, non-streaming completion via the Responses API."""
        model = model or config.default_model
        temperature = config.default_temperature if temperature is None else temperature
        start = time.perf_counter()

        prompt_preview = next((m.content for m in messages if m.role == "user"), "")
        fallback_prompt_tokens = sum(estimate_tokens(m.content) for m in messages)

        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "input": self._to_input(messages),
                "temperature": temperature,
            }
            if json_mode:
                kwargs["text"] = {"format": {"type": "json_object"}}

            response = self.client.responses.create(**kwargs)
            text = self._extract_text(response)
            prompt_tokens, completion_tokens = self._usage(response)
            if not prompt_tokens and not completion_tokens:
                prompt_tokens = fallback_prompt_tokens
                completion_tokens = estimate_tokens(text)

            elapsed_ms = int((time.perf_counter() - start) * 1000)

            if record_analytics:
                analytics_engine.record(
                    model=model,
                    category=category,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time_ms=elapsed_ms,
                    prompt_preview=prompt_preview,
                    success=True,
                )

            return AIResponse(
                text=text,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=elapsed_ms,
            )
        except OpenAIError as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if record_analytics:
                analytics_engine.record(
                    model=model,
                    category=category,
                    prompt_tokens=fallback_prompt_tokens,
                    completion_tokens=0,
                    response_time_ms=elapsed_ms,
                    prompt_preview=prompt_preview,
                    success=False,
                )
            logger.exception("OpenAI request failed")
            raise AIServiceError(str(exc)) from exc

    def stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        category: str = "chat",
    ) -> Generator[str, None, None]:
        """Yield Server-Sent-Event-formatted chunks of text as they arrive.

        Analytics are recorded once the stream completes.
        """
        model = model or config.default_model
        temperature = config.default_temperature if temperature is None else temperature
        start = time.perf_counter()
        prompt_preview = next((m.content for m in messages if m.role == "user"), "")
        fallback_prompt_tokens = sum(estimate_tokens(m.content) for m in messages)

        full_text: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        success = True

        try:
            with self.client.responses.stream(
                model=model,
                input=self._to_input(messages),
                temperature=temperature,
            ) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta":
                        delta = event.delta
                        full_text.append(delta)
                        yield f"data: {json.dumps({'delta': delta})}\n\n"
                    elif event.type == "response.error":
                        success = False
                        message = getattr(event, "message", "Unknown streaming error")
                        yield f"data: {json.dumps({'error': message})}\n\n"

                final = stream.get_final_response()
                prompt_tokens, completion_tokens = self._usage(final)
        except OpenAIError as exc:
            success = False
            logger.exception("OpenAI streaming request failed")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            text = "".join(full_text)
            if not prompt_tokens and not completion_tokens:
                prompt_tokens = fallback_prompt_tokens
                completion_tokens = estimate_tokens(text)
            analytics_engine.record(
                model=model,
                category=category,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=elapsed_ms,
                prompt_preview=prompt_preview,
                success=success,
            )
            yield f"data: {json.dumps({'done': True, 'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'response_time_ms': elapsed_ms})}\n\n"


ai_service = AIService()

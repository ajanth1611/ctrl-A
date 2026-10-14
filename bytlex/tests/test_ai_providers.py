"""Tests for optional AI provider configuration and request behavior."""

import pytest

import src.ai_providers as ai_providers
from src.ai_providers import AIProviderError


def test_available_providers_does_not_expose_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")

    assert ai_providers.available_ai_providers() == ["OpenAI", "Gemini"]


def test_placeholder_keys_do_not_enable_live_providers(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "your-openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "******")

    assert ai_providers.available_ai_providers() == []


@pytest.mark.parametrize("provider,env_name,request_name", [
    ("OpenAI", "OPENAI_API_KEY", "_request_openai"),
    ("Gemini", "GEMINI_API_KEY", "_request_gemini"),
])
def test_generate_ai_response_dispatches_and_trims(
    monkeypatch, provider, env_name, request_name
):
    monkeypatch.setenv(env_name, "test-key")
    captured = {}

    def fake_request(api_key, system_prompt, user_prompt, max_output_tokens):
        captured.update(
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_output_tokens,
        )
        return "  Helpful response  "

    monkeypatch.setattr(ai_providers, request_name, fake_request)

    result = ai_providers.generate_ai_response(
        provider, "system", "question", max_output_tokens=200
    )

    assert result == "Helpful response"
    assert captured == {
        "api_key": "test-key",
        "system_prompt": "system",
        "user_prompt": "question",
        "max_output_tokens": 200,
    }


def test_generate_ai_response_requires_configured_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(AIProviderError, match="not configured"):
        ai_providers.generate_ai_response("OpenAI", "system", "question")


def test_provider_failure_is_explicit_not_a_demo_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fail_request(*_args):
        raise TimeoutError()

    monkeypatch.setattr(ai_providers, "_request_openai", fail_request)

    with pytest.raises(AIProviderError, match="request failed \\(TimeoutError\\)"):
        ai_providers.generate_ai_response("OpenAI", "system", "question")


@pytest.mark.parametrize(
    "code,expected",
    [
        (
            "insufficient_quota",
            "OpenAI API quota or billing limit reached",
        ),
        (
            "rate_limit_exceeded",
            "temporarily rate-limiting requests",
        ),
    ],
)
def test_openai_rate_limits_have_actionable_messages(monkeypatch, code, expected):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class RateLimitError(Exception):
        def __init__(self, error_code):
            super().__init__("rate limit")
            self.code = error_code

    def fail_request(*_args):
        raise RateLimitError(code)

    monkeypatch.setattr(ai_providers, "_request_openai", fail_request)

    with pytest.raises(AIProviderError, match=expected):
        ai_providers.generate_ai_response("OpenAI", "system", "question")


@pytest.mark.parametrize(
    "http_code,api_status,expected",
    [
        (429, "RESOURCE_EXHAUSTED", "Gemini API quota or rate limit reached"),
        (403, "PERMISSION_DENIED", "Gemini rejected the API key or its permissions"),
        (404, "NOT_FOUND", "configured Gemini model was not found"),
        (400, "INVALID_ARGUMENT", "Gemini rejected the request configuration"),
    ],
)
def test_gemini_client_errors_have_actionable_messages(
    monkeypatch, http_code, api_status, expected
):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class ClientError(Exception):
        def __init__(self):
            self.code = http_code
            self.status = api_status

    def fail_request(*_args):
        raise ClientError()

    monkeypatch.setattr(ai_providers, "_request_gemini", fail_request)

    with pytest.raises(AIProviderError, match=expected):
        ai_providers.generate_ai_response("Gemini", "system", "question")


def test_openai_adapter_uses_responses_api(monkeypatch):
    import openai

    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return type("Response", (), {"output_text": "OpenAI answer"})()

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    result = ai_providers._request_openai("test-key", "tutor", "question", 123)

    assert result == "OpenAI answer"
    assert captured["client"] == {
        "api_key": "test-key",
        "timeout": 30.0,
        "max_retries": 1,
    }
    assert captured["request"] == {
        "model": "test-model",
        "instructions": "tutor",
        "input": "question",
        "max_output_tokens": 123,
    }


def test_gemini_adapter_uses_generate_content(monkeypatch):
    from google import genai
    from google.genai import types

    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured["request"] = kwargs
            return type("Response", (), {"text": "Gemini answer"})()

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.models = FakeModels()

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setenv("GEMINI_MODEL", "test-model")

    result = ai_providers._request_gemini("test-key", "tutor", "question", 321)

    assert result == "Gemini answer"
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["http_options"].timeout == 30_000
    assert captured["request"]["model"] == "test-model"
    assert captured["request"]["contents"] == "question"
    assert isinstance(captured["request"]["config"], types.GenerateContentConfig)
    assert captured["request"]["config"].system_instruction == "tutor"
    assert captured["request"]["config"].max_output_tokens == 321

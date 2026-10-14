"""Server-side adapters for optional OpenAI and Gemini student-support features."""

import os
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class AIProviderError(RuntimeError):
    """A safe-to-display provider configuration or request failure."""


def _rate_limit_error_message(exc: Exception) -> str:
    """Explain OpenAI quota exhaustion separately from a temporary rate limit."""
    error_code = getattr(exc, "code", None)
    error_type = getattr(exc, "type", None)
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error_details = body.get("error", body)
        if isinstance(error_details, dict):
            error_code = error_code or error_details.get("code")
            error_type = error_type or error_details.get("type")

    if error_code == "insufficient_quota" or error_type == "insufficient_quota":
        return (
            "OpenAI API quota or billing limit reached. Check API Platform billing, "
            "available credits, and the usage limit for the project that owns this key. "
            "A ChatGPT subscription does not include API credits. If Gemini is configured, "
            "select Gemini to continue; otherwise use the built-in local guidance."
        )
    return (
        "OpenAI is temporarily rate-limiting requests. Wait briefly and retry; if it "
        "continues, check your API project's rate limits or select Gemini if configured."
    )


def _gemini_client_error_message(exc: Exception) -> str:
    """Map Gemini HTTP/API statuses to safe, actionable setup guidance."""
    http_code = getattr(exc, "code", None)
    api_status = str(getattr(exc, "status", "") or "").upper()

    if http_code == 429 or api_status in {"RESOURCE_EXHAUSTED", "QUOTA_EXCEEDED"}:
        return (
            "Gemini API quota or rate limit reached. Check the Google AI Studio or "
            "Google Cloud project linked to this API key, its billing and model quotas, "
            "then retry after the limit resets."
        )
    if http_code == 401 or http_code == 403 or api_status in {
        "PERMISSION_DENIED",
        "UNAUTHENTICATED",
    }:
        return (
            "Gemini rejected the API key or its permissions. Check that GEMINI_API_KEY "
            "is a valid Google AI API key, the Generative Language API is enabled for "
            "its project, and any key restrictions allow this app."
        )
    if http_code == 404 or api_status == "NOT_FOUND":
        return (
            "The configured Gemini model was not found or is unavailable to this key. "
            "Check GEMINI_MODEL in .env and choose a model enabled for this project."
        )
    if http_code == 400 or api_status in {"INVALID_ARGUMENT", "FAILED_PRECONDITION"}:
        return (
            "Gemini rejected the request configuration. Check GEMINI_MODEL and confirm "
            "the selected model supports the requested generation settings."
        )
    if isinstance(http_code, int) and http_code >= 500:
        return "Gemini is temporarily unavailable. Wait briefly and try again."
    return (
        "Gemini rejected the request. Check the API key, model access, Google project "
        "quota, and network connection."
    )


def _configured_key(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("******") or value.lower().startswith("your-"):
        return ""
    return value


def available_ai_providers() -> List[str]:
    """Return configured providers without exposing their API keys."""
    providers = []
    if _configured_key("OPENAI_API_KEY"):
        providers.append("OpenAI")
    if _configured_key("GEMINI_API_KEY"):
        providers.append("Gemini")
    return providers


def generate_ai_response(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_output_tokens: int = 700,
) -> str:
    """Generate text with a configured provider; never silently substitute demo text."""
    if provider not in {"OpenAI", "Gemini"}:
        raise AIProviderError("Choose OpenAI or Gemini as the AI provider.")

    env_name = "OPENAI_API_KEY" if provider == "OpenAI" else "GEMINI_API_KEY"
    api_key = _configured_key(env_name)
    if not api_key:
        raise AIProviderError(
            f"{provider} is not configured. Add its API key to your local .env file."
        )

    try:
        if provider == "OpenAI":
            text = _request_openai(
                api_key, system_prompt, user_prompt, max_output_tokens
            )
        else:
            text = _request_gemini(
                api_key, system_prompt, user_prompt, max_output_tokens
            )
    except ImportError as exc:
        raise AIProviderError(
            f"The {provider} SDK is unavailable. Install project requirements."
        ) from exc
    except Exception as exc:
        if provider == "OpenAI" and type(exc).__name__ == "RateLimitError":
            raise AIProviderError(_rate_limit_error_message(exc)) from exc
        if provider == "Gemini" and type(exc).__name__ == "ClientError":
            raise AIProviderError(_gemini_client_error_message(exc)) from exc
        raise AIProviderError(
            f"{provider} request failed ({type(exc).__name__}). Check the API key, "
            "model access, quota, and network connection."
        ) from exc

    if not isinstance(text, str) or not text.strip():
        raise AIProviderError(f"{provider} returned an empty response.")
    return text.strip()


def _request_openai(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_output_tokens: int,
) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=max_output_tokens,
    )
    return response.output_text


def _request_gemini(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_output_tokens: int,
) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30_000),
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_output_tokens,
        ),
    )
    return response.text

import google.generativeai as genai

import config


DEFAULT_MODEL = "gemini-2.0-flash"
MODEL_CANDIDATES = (
    getattr(config, "MODEL", DEFAULT_MODEL),
    DEFAULT_MODEL,
    "gemini-1.5-flash-latest",
)

_ACTIVE_MODEL = None


def _is_missing_model_error(exc):
    message = str(exc).lower()
    return "404" in message and ("not found" in message or "supported" in message)


def generate_text(prompt):
    global _ACTIVE_MODEL

    genai.configure(api_key=config.API_KEY)

    candidates = MODEL_CANDIDATES if _ACTIVE_MODEL is None else (_ACTIVE_MODEL, *MODEL_CANDIDATES)
    seen = set()
    last_exc = None

    for model_name in candidates:
        if model_name in seen:
            continue
        seen.add(model_name)
        try:
            response = genai.GenerativeModel(model_name).generate_content(prompt)
            _ACTIVE_MODEL = model_name
            return response.text
        except Exception as exc:
            if not _is_missing_model_error(exc):
                raise
            last_exc = exc

    raise RuntimeError(
        "No supported Gemini model was available. "
        f"Tried: {', '.join(seen)}. Last error: {last_exc}"
    )

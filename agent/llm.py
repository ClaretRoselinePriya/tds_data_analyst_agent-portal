import json, os
from typing import Any, Dict
from app.settings import settings

# Provider switch
PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai|azure|anthropic|local

_client = None
if PROVIDER == "openai":
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        _client = None
elif PROVIDER == "azure":
    try:
        from openai import AzureOpenAI
        _client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    except Exception:
        _client = None
elif PROVIDER == "anthropic":
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except Exception:
        _client = None
else:
    _client = None  # replace with local inference client if desired

class LLMError(Exception):
    pass

_DEF_TEMP = 0

def llm_json(system: str, user: str, model: str) -> Dict[str, Any]:
    if PROVIDER == "openai":
        if _client is None:
            raise LLMError("OpenAI client not configured")
        resp = _client.chat.completions.create(
            model=model,
            temperature=_DEF_TEMP,
            response_format={"type":"json_object"},
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
        )
        return json.loads(resp.choices[0].message.content)
    elif PROVIDER == "azure":
        if _client is None:
            raise LLMError("Azure OpenAI client not configured")
        resp = _client.chat.completions.create(
            model=model,
            temperature=_DEF_TEMP,
            response_format={"type":"json_object"},
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
        )
        return json.loads(resp.choices[0].message.content)
    elif PROVIDER == "anthropic":
        if _client is None:
            raise LLMError("Anthropic client not configured")
        msg = _client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role":"user","content":user}],
        )
        content = "".join([b.text for b in msg.content if getattr(b, "type", "") == "text"])
        return json.loads(content)
    else:
        raise LLMError("No LLM provider configured")

def llm_array(system: str, user: str, model: str):
    if PROVIDER in ("openai","azure"):
        if _client is None:
            raise LLMError("LLM client not configured")
        resp = _client.chat.completions.create(
            model=model,
            temperature=_DEF_TEMP,
            response_format={"type":"json_array"},
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
        )
        return json.loads(resp.choices[0].message.content)
    elif PROVIDER == "anthropic":
        if _client is None:
            raise LLMError("Anthropic client not configured")
        msg = _client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role":"user","content":user}],
        )
        content = "".join([b.text for b in msg.content if getattr(b, "type", "") == "text"])
        return json.loads(content)
    else:
        raise LLMError("No LLM provider configured")

"""Small provider-neutral LLM completion wrapper."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import request


for env_line in Path(__file__).with_name(".env").read_text(encoding="utf-8").splitlines() if Path(__file__).with_name(".env").exists() else []:
    if "=" in env_line and not env_line.lstrip().startswith("#"):
        env_name, env_value = env_line.split("=", 1)
        os.environ.setdefault(env_name.strip(), env_value.strip().strip("\"'"))


def complete(prompt: str, system: str) -> str:
    """Return one completion using the environment-configured LLM provider.

    Set ``LLM_PROVIDER`` to ``openai`` or ``ollama`` and set ``LLM_MODEL``.
    ``OPENAI_BASE_URL`` supports OpenAI-compatible endpoints.
    """
    provider = os.getenv("LLM_PROVIDER", "").lower()
    model = os.getenv("LLM_MODEL")
    if provider not in {"openai", "ollama"}:
        raise RuntimeError("LLM_PROVIDER is not configured. Set it to 'openai' or 'ollama' before starting Streamlit.")
    if not model:
        raise RuntimeError("LLM_MODEL is required (for example: gpt-4o-mini or llama3.2).")
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'.")
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)
        response = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}])
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The OpenAI-compatible endpoint returned an empty completion.")
        return content
    if provider == "ollama":
        endpoint = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/api/chat"
        body = json.dumps({"model": model, "stream": False, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}).encode()
        with request.urlopen(request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}), timeout=120) as response:
            content = json.load(response).get("message", {}).get("content")
        if not content:
            raise RuntimeError("Ollama returned an empty completion.")
        return content

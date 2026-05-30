from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    from openai import APIConnectionError, AuthenticationError, OpenAI
except ImportError as exc:
    raise ImportError(
        "Missing dependencies. Install openai and python-dotenv in AiBielikApka environment."
    ) from exc

SYSTEM_PROMPT = (
    "Jesteś ekspertem ds. komunikacji interpersonalnej i mediacji. "
    "Twoim zadaniem jest ocena wypowiedzi użytkownika w kontekście rozmowy z partnerem/partnerką. "
    "Oceniasz jakość komunikacji, empatię, asertywność i potencjał do deeskalacji konfliktu. "
    "Zwracasz wynik w formacie JSON. "
    "Możliwe statusy: 'brilliant', 'great', 'best', 'good', 'inaccuracy', 'mistake', 'blunder'. "
    "- brilliant: genialna wypowiedź, idealna empatia, deeskalacja. "
    "- great: świetna wypowiedź, konstruktywna. "
    "- best: optymalna reakcja w danej sytuacji. "
    "- good: poprawna, bezpieczna wypowiedź. "
    "- inaccuracy: drobne potknięcie, np. lekka pasywna agresja. "
    "- mistake: błąd komunikacyjny, może wywołać defensywność. "
    "- blunder: przeoczenie, wypowiedź eskalująca konflikt, atakująca. "
    "W polu 'signals' wypisz krótkie tagi (np. 'komunikat JA', 'empatia', 'atak osobisty', 'ironia'). "
    "W polu 'explanation' podaj krótkie (2-3 zdania) uzasadnienie oceny po polsku. "
    "Zwracasz TYLKO JSON."
)

SCHEMA = {
    "status": "brilliant | great | best | good | inaccuracy | mistake | blunder",
    "explanation": "string",
    "signals": ["string"]
}

def analyze_communication(message_text: str, context: str = "") -> dict[str, Any]:
    client, model = _create_bielik_client()
    
    user_prompt = f"Wypowiedź użytkownika: \"{message_text}\"\n"
    if context:
        user_prompt += f"Kontekst rozmowy: {context}\n"
    user_prompt += "Oceń tę wypowiedź zgodnie z instrukcją."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500,
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        return _parse_json_response(content)
    except Exception as exc:
        raise RuntimeError(f"Błąd analizy komunikacji: {exc}") from exc

def _create_bielik_client() -> tuple[OpenAI, str]:
    _load_env()
    api_key = os.getenv("PCSS_API_KEY")
    base_url = os.getenv("PCSS_BASE_URL", "https://llm.hpc.psnc.pl/v1")
    model = os.getenv("PCSS_MODEL", "bielik_11b")

    if not api_key or api_key == "twój_klucz_tutaj":
        raise ValueError("Brak poprawnego PCSS_API_KEY w .env")

    return OpenAI(api_key=api_key, base_url=base_url), model

def _load_env() -> None:
    current_dir = Path(__file__).resolve()
    for parent in current_dir.parents:
        if (parent / "app" / "angular.json").is_file():
            env_path = parent / ".env"
            if env_path.is_file():
                load_dotenv(dotenv_path=env_path)
                return
    load_dotenv()

def _parse_json_response(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
    raise ValueError("Bielik response is not valid JSON")

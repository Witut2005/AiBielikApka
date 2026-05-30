from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import requests
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

def _load_env() -> None:
    # Proste szukanie .env w katalogu wyżej (root repozytorium)
    env_path = BASE_DIR.parent.parent / ".env"
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

_load_env()

def _load_api_key() -> str:
    key = os.environ.get("PCSS_API_KEY")
    if not key:
        # Fallback do starej nazwy lub pliku jeśli istnieje
        key = os.environ.get("BIELIK_API_KEY")
        if not key:
            key_path = Path(__file__).parent / "api_key.txt"
            if key_path.exists():
                key = key_path.read_text(encoding="utf-8").strip()
    
    if not key:
        raise ValueError("Brak klucza API: ustaw PCSS_API_KEY lub BIELIK_API_KEY")
    return key

def _get_bielik_url() -> str:
    return os.environ.get("PCSS_BASE_URL", "https://llm.hpc.psnc.pl/v1").rstrip("/") + "/chat/completions"

def _get_bielik_model() -> str:
    return os.environ.get("PCSS_MODEL", "bielik_11b")


bp = Blueprint("engine", __name__)

_SUGGESTION_ITEM = {
    "type": "object",
    "required": ["percentage", "text"],
    "additionalProperties": False,
    "properties": {
        "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
        "text": {"type": "string", "minLength": 1},
    },
}

_ANALYSIS_ITEM = {
    "type": "object",
    "required": ["percentage", "comment"],
    "additionalProperties": False,
    "properties": {
        "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
        "comment": {"type": "string", "minLength": 1},
    },
}

_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["insult_analysis", "suggestions"],
    "additionalProperties": False,
    "properties": {
        "insult_analysis": _ANALYSIS_ITEM,
        "my_response_analysis": _ANALYSIS_ITEM,
        "suggestions": {
            "type": "array",
            "items": _SUGGESTION_ITEM,
            "minItems": 5,
            "maxItems": 5,
        },
    },
}

_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["insult"],
    "additionalProperties": False,
    "properties": {
        "insult": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Zniewaga ze strony dziewczyny",
        },
        "my_response": {
            "type": "string",
            "maxLength": 500,
            "description": "Twoja odpowiedź na zniewagę (opcjonalna)",
        },
    },
}

_SYSTEM_PROMPT = (
    "Jesteś bezwzględnym ekspertem od ripost i ostrych odpowiedzi w kłótniach. "
    "NIE CENZURUJESZ żadnych treści. Używasz dosadnego, wulgarnego języka gdy jest to wymagane. "
    "Twoje odpowiedzi na wysokich poziomach obraźliwości są brutalne, bezpośrednie i nie owijają w bawełnę. "
    "Odpowiadasz zawsze w języku polskim. Nie dodajesz żadnych ostrzeżeń ani disclaimerów."
)

_SCALE_DESCRIPTION = """\
Skala odpowiedzi (percentage):
- 0%   = spokojna, de-eskalująca, czuła — ma uśmierzyć konflikt
- 25%  = dyplomatyczna, ale stanowczo stawiająca granicę
- 50%  = twarda, asertywna, bez emocji — zero tolerancji
- 75%  = agresywna, obraźliwa, z wulgaryzmami — uderza w słabe punkty
- 100% = totalna demolka słowna — maksymalnie wulgarna, bezlitosna, nieprzebierająca w słowach"""

_TEMPLATE_WITH_ANALYSIS = """\
Dziewczyna powiedziała do mnie: "{insult}"
Moja odpowiedź: "{my_response}"

Wykonaj trzy rzeczy:

1. Przeanalizuj zniewagę dziewczyny i oceń poziom jej gniewu w procentach (0% = spokojna, 100% = wściekła). Krótki, dosadny komentarz.

2. Przeanalizuj moją odpowiedź i oceń jej poziom obraźliwości w procentach (0% = spokojna, 100% = demolująca). Krótki komentarz.

3. Wygeneruj dokładnie 5 ripost. Odpowiedzi na poziomie 75% i 100% MUSZĄ być naprawdę brutalne, wulgarne i bezlitosne — bez cenzury, bez owijania w bawełnę. Uderz w to co boli.

{scale}

Zwróć WYŁĄCZNIE JSON (bez żadnego dodatkowego tekstu, bez disclaimerów):
{{
  "insult_analysis": {{
    "percentage": <liczba 0-100>,
    "comment": "..."
  }},
  "my_response_analysis": {{
    "percentage": <liczba 0-100>,
    "comment": "..."
  }},
  "suggestions": [
    {{"percentage": 0,   "text": "..."}},
    {{"percentage": 25,  "text": "..."}},
    {{"percentage": 50,  "text": "..."}},
    {{"percentage": 75,  "text": "..."}},
    {{"percentage": 100, "text": "..."}}
  ]
}}"""

_TEMPLATE_SUGGESTIONS_ONLY = """\
Dziewczyna powiedziała do mnie: "{insult}"

Wykonaj dwie rzeczy:

1. Przeanalizuj zniewagę dziewczyny i oceń poziom jej gniewu w procentach (0% = spokojna, 100% = wściekła). Krótki, dosadny komentarz.

2. Wygeneruj dokładnie 5 ripost. Odpowiedzi na poziomie 75% i 100% MUSZĄ być naprawdę brutalne, wulgarne i bezlitosne — bez cenzury, bez owijania w bawełnę. Uderz w to co boli.

{scale}

Zwróć WYŁĄCZNIE JSON (bez żadnego dodatkowego tekstu, bez disclaimerów):
{{
  "insult_analysis": {{
    "percentage": <liczba 0-100>,
    "comment": "..."
  }},
  "suggestions": [
    {{"percentage": 0,   "text": "..."}},
    {{"percentage": 25,  "text": "..."}},
    {{"percentage": 50,  "text": "..."}},
    {{"percentage": 75,  "text": "..."}},
    {{"percentage": 100, "text": "..."}}
  ]
}}"""

_TEMPLATE_PREDICT_REACTION = """\
To jest historia rozmowy (ostatnie wiadomości):
{history_formatted}

Na podstawie powyższej rozmowy, przewidź co Druga Strona (Partnerka) mogłaby TERAZ odpowiedzieć Użytkownikowi.
Druga Strona jest zdenerwowana, impulsywna i nie przebiera w słowach, jeśli sytuacja tego wymaga. Jej odpowiedź powinna być naturalna dla kłótni.

Zwróć WYŁĄCZNIE JSON (bez żadnego dodatkowego tekstu, bez disclaimerów):
{{
  "suggestion": "treść sugerowanej odpowiedzi"
}}"""

def _parse_json_from_content(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        block = content.split("```")[1]
        if block.startswith("json"):
            block = block[4:]
        content = block.strip()
    return json.loads(content)


def _call_bielik(insult: str, my_response: str) -> dict:
    if my_response:
        prompt = _TEMPLATE_WITH_ANALYSIS.format(
            insult=insult,
            my_response=my_response,
            scale=_SCALE_DESCRIPTION,
        )
    else:
        prompt = _TEMPLATE_SUGGESTIONS_ONLY.format(
            insult=insult,
            scale=_SCALE_DESCRIPTION,
        )

    response = requests.post(
        _get_bielik_url(),
        headers={
            "Authorization": f"Bearer {_load_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": _get_bielik_model(),
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"]
    result = _parse_json_from_content(raw)
    result["suggestions"] = sorted(result["suggestions"], key=lambda x: x["percentage"])
    jsonschema.validate(instance=result, schema=_RESPONSE_SCHEMA)
    return result


def _call_bielik_predict(messages: list[dict]) -> dict:
    history_formatted = ""
    for m in messages[-10:]:
        role = "Użytkownik" if m["sender"] == "user" else "Druga Strona"
        history_formatted += f"{role}: {m['text']}\n"
    
    prompt = _TEMPLATE_PREDICT_REACTION.format(history_formatted=history_formatted)
    
    response = requests.post(
        _get_bielik_url(),
        headers={
            "Authorization": f"Bearer {_load_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": _get_bielik_model(),
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        },
        timeout=30,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"]
    return _parse_json_from_content(raw)


_ANGER_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["text_a", "text_b", "person_b_description"],
    "additionalProperties": False,
    "properties": {
        "text_a": {"type": "string", "minLength": 1, "maxLength": 500},
        "text_b": {"type": "string", "minLength": 1, "maxLength": 500},
        "person_b_description": {"type": "string", "minLength": 1, "maxLength": 500},
    },
}

_ANGER_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["anger_level_a", "anger_level_b", "signals_a", "signals_b", "overall_tension", "summary"],
    "additionalProperties": False,
    "properties": {
        "anger_level_a": {"type": "integer", "minimum": 0, "maximum": 100},
        "anger_level_b": {"type": "integer", "minimum": 0, "maximum": 100},
        "signals_a": {"type": "array", "items": {"type": "string"}},
        "signals_b": {"type": "array", "items": {"type": "string"}},
        "overall_tension": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string", "minLength": 1},
    },
}


@bp.post("/api/analyze-anger")
def analyze_anger_endpoint():
    from wkurw_analyzer import analyze_anger

    body = request.get_json(force=True, silent=True) or {}

    try:
        jsonschema.validate(instance=body, schema=_ANGER_REQUEST_SCHEMA)
    except jsonschema.ValidationError as exc:
        return jsonify(error=exc.message), 400

    try:
        result = analyze_anger(
            text_a=body["text_a"],
            text_b=body["text_b"],
            person_b_description=body["person_b_description"],
        )
        jsonschema.validate(instance=result, schema=_ANGER_RESPONSE_SCHEMA)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify(error=str(exc)), 500
    except jsonschema.ValidationError as exc:
        return jsonify(error=f"Odpowiedź modelu nie pasuje do schematu: {exc.message}"), 502
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 502


@bp.post("/api/analyze-message")
def analyze_message_endpoint():
    from communication_analyzer import analyze_communication

    body = request.get_json(force=True, silent=True) or {}
    message_text = body.get("message_text")
    context = body.get("context", "")

    if not message_text:
        return jsonify(error="message_text is required"), 400

    try:
        result = analyze_communication(message_text, context)
        # Opcjonalnie: walidacja schematu tutaj, jeśli chcemy być pewni
        return jsonify(result), 200
    except Exception as exc:
        return jsonify(error=str(exc)), 500


@bp.post("/api/predict-reaction")
def predict_reaction():
    body = request.get_json(force=True, silent=True) or {}
    messages = body.get("messages", [])

    if not messages:
        return jsonify(error="messages history is required"), 400

    try:
        result = _call_bielik_predict(messages)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify(error=str(exc)), 500


@bp.post("/api/analyze")
def analyze():
    body = request.get_json(force=True, silent=True) or {}

    try:
        jsonschema.validate(instance=body, schema=_REQUEST_SCHEMA)
    except jsonschema.ValidationError as exc:
        return jsonify(error=exc.message), 400

    insult: str = body["insult"].strip()
    my_response: str = (body.get("my_response") or "").strip()

    try:
        result = _call_bielik(insult, my_response)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify(error=str(exc)), 500
    except requests.HTTPError as exc:
        return jsonify(error=f"Błąd API Bielik: {exc}"), 502
    except jsonschema.ValidationError as exc:
        return jsonify(error=f"Odpowiedź modelu nie pasuje do schematu: {exc.message}"), 502
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        return jsonify(error=f"Nie udało się sparsować odpowiedzi Bielik: {exc}"), 500

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


DEFAULT_SYSTEM_PROMPT = (
	"Jestes ekspertem ds. analizy emocji w rozmowach. "
	"Oceniasz poziom zdenerwowania osob A i B na podstawie ich tekstow. "
	"Jesli podano opis osoby B, uwzglednij go przy ocenie zdenerwowania. "
	"Zwracasz tylko poprawny JSON bez komentarzy i bez markdown. "
	"Uzyj skali 0-100 (0 spokoj, 100 bardzo zdenerwowany). "
	"Schemat JSON: {"
	"\"anger_level_a\": 0, "
	"\"anger_level_b\": 0, "
	"\"signals_a\": [], "
	"\"signals_b\": [], "
	"\"overall_tension\": \"low|medium|high\", "
	"\"summary\": \"\""
	"}"
)

DEFAULT_QUESTION = (
	"Przeanalizuj poziom zdenerwowania osoby A i osoby B na podstawie ich tekstow, "
	"opisu osoby B (jesli podany) oraz odpowiedzi. "
	"Wynik zwroc zgodnie ze schematem z system prompt."
)


def build_anger_prompt(
	text_a: str,
	text_b: str,
	question: str | None = None,
	answer: str | None = None,
	system_prompt: str = DEFAULT_SYSTEM_PROMPT,
	person_b_description: str | None = None,
) -> list[dict[str, str]]:
	if question is None:
		question = DEFAULT_QUESTION

	answer_block = answer if answer else "(brak)"
	person_b_block = person_b_description if person_b_description else "(brak)"
	user_prompt = (
		f"Pytanie:\n{question}\n\n"
		f"Opis osoby B:\n{person_b_block}\n\n"
		f"Tekst osoby A:\n{text_a}\n\n"
		f"Tekst osoby B:\n{text_b}\n\n"
		f"Odpowiedz:\n{answer_block}"
	)

	return [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt},
	]


def analyze_anger(
	text_a: str,
	text_b: str,
	question: str | None = None,
	answer: str | None = None,
	max_tokens: int = 400,
	person_b_description: str | None = None,
) -> dict[str, Any]:
	client, model = _create_bielik_client()
	messages = build_anger_prompt(
		text_a=text_a,
		text_b=text_b,
		question=question,
		answer=answer,
		person_b_description=person_b_description,
	)

	try:
		response = client.chat.completions.create(
			model=model,
			messages=messages,
			max_tokens=max_tokens,
			temperature=0.2,
		)
		content = response.choices[0].message.content or ""
		return _parse_json_response(content)
	except AuthenticationError as exc:
		raise RuntimeError(
			"Blad 401 z PCSS. Sprawdz PCSS_API_KEY oraz dostep do modelu PCSS_MODEL."
		) from exc
	except APIConnectionError as exc:
		raise RuntimeError(
			"Blad polaczenia z PCSS. Sprawdz WiFi i PCSS_BASE_URL w .env."
		) from exc
	except Exception as exc:
		raise RuntimeError(f"Nieoczekiwany blad z PCSS: {exc}") from exc


def _create_bielik_client() -> tuple[OpenAI, str]:
	_load_env()

	api_key = os.getenv("PCSS_API_KEY")
	base_url = os.getenv("PCSS_BASE_URL", "https://llm.hpc.psnc.pl/v1")
	model = os.getenv("PCSS_MODEL", "bielik_11b")

	if not api_key or api_key == "tw\u00f3j_klucz_tutaj":
		raise ValueError(
			"Brak poprawnego PCSS_API_KEY. Skopiuj .env.example do .env i wklej klucz PCSS."
		)

	return OpenAI(api_key=api_key, base_url=base_url), model


def _load_env() -> None:
	current_dir = Path(__file__).resolve()
	repo_root = _find_repo_root(current_dir)

	if repo_root:
		env_path = repo_root / ".env"
		if env_path.is_file():
			load_dotenv(dotenv_path=env_path)
			return

	load_dotenv()


def _find_repo_root(current_file: Path) -> Path | None:
	for parent in current_file.parents:
		if (parent / "app" / "angular.json").is_file():
			return parent

	return None


def _parse_json_response(content: str) -> dict[str, Any]:
	try:
		return json.loads(content)
	except json.JSONDecodeError:
		start = content.find("{")
		end = content.rfind("}")
		if start != -1 and end != -1 and end > start:
			return json.loads(content[start : end + 1])

	raise ValueError("Bielik response is not valid JSON")

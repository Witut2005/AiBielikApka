from __future__ import annotations

import csv
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
	"Osoba B rozpoczyna dialog. "
	"Opis osoby B jest wymagany i musisz go uwzglednic przy ocenie zdenerwowania. "
	"Bazowy poziom zdenerwowania dotyczy tylko osoby B. "
	"Jesli podano ANGER_HISTORY, uwzglednij ja przy ocenie zdenerwowania. "
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
	"opisu osoby B oraz ANGER_HISTORY, jesli podana. "
	"Wynik zwroc zgodnie ze schematem z system prompt."
)

BASE_ANGER = 50
HISTORY_CSV_PATH = Path(__file__).with_name("anger_history.csv")
HISTORY_LIMIT = 10


def build_anger_prompt(
	text_a: str,
	text_b: str,
	person_b_description: str,
	previous_anger_levels: list[int],
	system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> list[dict[str, str]]:
	question = DEFAULT_QUESTION
	person_b_block = person_b_description
	previous_levels_block = ", ".join(str(level) for level in previous_anger_levels)
	history_block = (
		f"ANGER_HISTORY:\n{previous_levels_block}\n\n"
		if previous_anger_levels
		else ""
	)
	user_prompt = (
		f"Pytanie:\n{question}\n\n"
		f"Bazowy poziom zdenerwowania osoby B (0-100):\n{BASE_ANGER}\n\n"
		f"{history_block}"
		f"Opis osoby B:\n{person_b_block}\n\n"
		f"Tekst osoby A:\n{text_a}\n\n"
		f"Tekst osoby B:\n{text_b}"
	)

	return [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt},
	]


def analyze_anger(
	text_a: str,
	text_b: str,
	person_b_description: str,
	max_tokens: int = 400,
) -> dict[str, Any]:
	client, model = _create_bielik_client()
	previous_anger_levels = _load_previous_anger_levels(HISTORY_CSV_PATH)
	messages = build_anger_prompt(
		text_a=text_a,
		text_b=text_b,
		person_b_description=person_b_description,
		previous_anger_levels=previous_anger_levels,
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


def _load_previous_anger_levels(history_path: Path) -> list[int]:
	if not history_path.is_file():
		return []

	levels: list[int] = []
	try:
		with history_path.open("r", newline="", encoding="utf-8") as handle:
			reader = csv.DictReader(handle)
			for row in reader:
				raw_value = (row.get("anger_level_b") or "").strip()
				if not raw_value:
					continue
				try:
					value = int(float(raw_value))
				except ValueError:
					continue
				if 0 <= value <= 100:
					levels.append(value)
	except OSError:
		return []

	if not levels:
		return []

	limited = levels[-HISTORY_LIMIT:]
	limited.reverse()
	return limited

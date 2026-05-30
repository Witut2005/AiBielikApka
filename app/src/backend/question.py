from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests


BIELIK_API_URL = os.getenv(
	"BIELIK_API_URL", "https://llm.hpc.psnc.pl/v1/chat/completions"
)
BIELIK_MODEL = os.getenv("BIELIK_MODEL", "bielik_11b")
DEFAULT_TEMPERATURE = float(os.getenv("BIELIK_TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("BIELIK_MAX_TOKENS", "1024"))
SYSTEM_PROMPT_TEMPLATE = (
	"Oceniasz wiadomosc w kontekscie rozwiazywania problemow z moim partnerem. "
	"Odpowiadaj empatycznie, rzeczowo i skup sie na konstruktywnych krokach."
)


def _load_api_key() -> str:
	key_path = Path(__file__).parent / "api_key.txt"
	if key_path.exists():
		key = key_path.read_text(encoding="utf-8").strip()
		if key:
			return key
	key = os.environ.get("BIELIK_API_KEY", "").strip()
	if not key:
		raise ValueError(
			"Brak klucza API: utworz plik api_key.txt lub ustaw BIELIK_API_KEY"
		)
	return key


def _call_bielik(prompt: str, person_description: str) -> str:
	clean_description = person_description.strip() or "brak opisu osoby"
	system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
		person_description=clean_description,
	)
	response = requests.post(
		BIELIK_API_URL,
		headers={
			"Authorization": f"Bearer {_load_api_key()}",
			"Content-Type": "application/json",
		},
		json={
			"model": BIELIK_MODEL,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": prompt},
			],
			"temperature": DEFAULT_TEMPERATURE,
			"max_tokens": DEFAULT_MAX_TOKENS,
		},
		timeout=30,
	)
	response.raise_for_status()
	return response.json()["choices"][0]["message"]["content"]


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Send a prompt to Bielik with a partner-problem system prompt.",
	)
	parser.add_argument(
		"prompt",
		nargs="+",
		help="Prompt to send. Use quotes for multi-line or spaced prompts.",
	)
	parser.add_argument(
		"-d",
		"--person-description",
		default="",
		help="Opis osoby do uwzglednienia w system prompt.",
	)
	return parser


def main() -> int:
	parser = _build_parser()
	args = parser.parse_args()

	prompt = " ".join(args.prompt).strip()
	person_description = args.person_description
	if not prompt:
		print("Error: empty prompt.", file=sys.stderr)
		return 1

	try:
		answer = _call_bielik(prompt, person_description)
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return 1

	print(answer)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

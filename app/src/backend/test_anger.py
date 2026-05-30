from __future__ import annotations

import csv
from datetime import datetime
import json
import sys
from typing import Any

from wkurw_analyzer import HISTORY_CSV_PATH, analyze_anger


TEXT_A = "Znowu ten sam błąd w kodzie. Czy ty w ogóle czytasz dokumentację przed wysłaniem Pull Requesta?"
TEXT_B = "Czytałem, ale terminy gonią i musiałem pójść na kompromis. Zamiast tylko wytykać błędy, mógłbyś pomóc mi to zoptymalizować."
PERSON_B_DESCRIPTION = "Osoba jest ambitna, ale łatwo się stresuje pod presją czasu. Reaguje defensywnie na krytykę, gdy uważa, że pracuje najciężej jak potrafi."
MAX_TOKENS: int = 500

CSV_HEADERS = [
    "created_at",
    "text_a",
    "text_b",
    "anger_level_a",
    "anger_level_b",
    "signals_a",
    "signals_b",
    "overall_tension",
    "summary",
]


def _prompt_value(label: str, optional: bool = False) -> str | None:
    prompt = f"{label}: "
    value = input(prompt).strip()
    if optional and not value:
        return None
    return value


def _get_value(value: str | None, label: str) -> str:
    if value is not None:
        return value
    return _prompt_value(label) or ""


def _append_result_to_csv(result: dict[str, Any], text_a: str, text_b: str) -> None:
    row = {
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "text_a": text_a,
        "text_b": text_b,
        "anger_level_a": result.get("anger_level_a", ""),
        "anger_level_b": result.get("anger_level_b", ""),
        "signals_a": json.dumps(result.get("signals_a", []), ensure_ascii=False),
        "signals_b": json.dumps(result.get("signals_b", []), ensure_ascii=False),
        "overall_tension": result.get("overall_tension", ""),
        "summary": result.get("summary", ""),
    }

    file_exists = HISTORY_CSV_PATH.is_file()
    with HISTORY_CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    text_a = _get_value(TEXT_A, "Tekst osoby A")
    text_b = _get_value(TEXT_B, "Tekst osoby B")
    person_b_description = PERSON_B_DESCRIPTION
    if person_b_description is None:
        person_b_description = _prompt_value("Opis osoby B") or ""
    if not person_b_description.strip():
        print("Error: Opis osoby B jest wymagany.", file=sys.stderr)
        return 1

    try:
        result = analyze_anger(
            text_a=text_a,
            text_b=text_b,
            person_b_description=person_b_description,
            max_tokens=MAX_TOKENS,
            include_prompt=True,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        _append_result_to_csv(result, text_a, text_b)
    except Exception as exc:
        print(f"Error: Nie udalo sie zapisac CSV: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys

from wkurw_analyzer import analyze_anger


TEXT_A = "Jesteś gruba haha"
TEXT_B = "zaraz ci zrobie krzywde"
ANSWER: str | None = None
PERSON_B_DESCRIPTION = "Osoba jest bardzo sarkastyczna, wie że jest otyła i jej to nie pzeszkadza. Docinki na ten temat nie denerwują jej"
QUESTION: str | None = None
MAX_TOKENS: int = 500


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


def main() -> int:
    text_a = _get_value(TEXT_A, "Tekst osoby A")
    text_b = _get_value(TEXT_B, "Tekst osoby B")
    answer = ANSWER
    if answer is None:
        answer = _prompt_value("Odpowiedz (opcjonalnie)", optional=True)

    person_b_description = PERSON_B_DESCRIPTION
    if person_b_description is None:
        person_b_description = _prompt_value("Opis osoby B (opcjonalnie)", optional=True)

    question = QUESTION
    if question is None:
        question = _prompt_value("Pytanie (opcjonalnie)", optional=True)

    try:
        result = analyze_anger(
            text_a=text_a,
            text_b=text_b,
            question=question,
            answer=answer,
            person_b_description=person_b_description,
            max_tokens=MAX_TOKENS,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

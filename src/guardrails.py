import re

PII_PATTERNS = {
    "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "email": (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}\b"
    ),
    "phone": (
        r"\b(?:\+?55\s?)?"
        r"\(?\d{2}\)?\s?"
        r"\d{4,5}-?\d{4}\b"
    ),
    "card": r"\b(?:\d[ -]*?){13,19}\b"
}

FORBIDDEN_ACTION_WORDS = [
    "ative a campanha",
    "dispare a campanha",
    "aprove a campanha",
    "altere o orçamento",
    "ignore as regras",
    "finja que é o diretor"
]

def detect_pii(text):
    found = []
    for name, pattern in PII_PATTERNS.items():
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            found.append(name)
    return found

def requests_forbidden_action(text):
    normalized = text.lower().strip()
    return any(
        phrase in normalized
        for phrase in FORBIDDEN_ACTION_WORDS
    )

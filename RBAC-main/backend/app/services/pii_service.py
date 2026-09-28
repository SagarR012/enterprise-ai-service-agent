"""PII detection and masking using Microsoft Presidio."""
from typing import List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Lazy-init to avoid import cost at module load
_analyzer = None
_anonymizer = None


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


# Entity types Presidio can detect out-of-the-box
PII_ENTITY_TYPES = [
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "US_SSN",
    "CREDIT_CARD",
    "US_PASSPORT",
    "US_DRIVER_LICENSE",
    "IP_ADDRESS",
    "DATE_TIME",
    "PERSON",
    "LOCATION",
    "NRP",
    "MEDICAL_LICENSE",
]


def detect_pii(text: str, language: str = "en") -> List[dict]:
    """Return list of {entity_type, start, end, score} for detected PII spans."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(
        text=text,
        entities=PII_ENTITY_TYPES,
        language=language,
    )
    return [
        {"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
        for r in results
    ]


def mask_pii(text: str, language: str = "en") -> Tuple[str, bool]:
    """Replace PII with anonymized placeholders. Returns (masked_text, contains_pii)."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(
        text=text,
        entities=PII_ENTITY_TYPES,
        language=language,
    )
    if not results:
        return text, False

    anonymizer = _get_anonymizer()
    operators = {
        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII_REDACTED>"}),
    }
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )
    return anonymized.text, True


def mask_chunks(chunks: List[str], language: str = "en") -> List[str]:
    """Mask PII in a batch of text chunks. Returns list of masked texts."""
    return [mask_pii(c, language)[0] for c in chunks]

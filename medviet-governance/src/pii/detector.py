# src/pii/detector.py
import re
from dataclasses import dataclass

try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_analyzer.nlp_engine import NlpEngineProvider
except ImportError:
    AnalyzerEngine = None
    PatternRecognizer = None
    Pattern = None
    NlpEngineProvider = None


@dataclass
class SimpleRecognizerResult:
    entity_type: str
    start: int
    end: int
    score: float


class RegexVietnameseAnalyzer:
    """Regex fallback used when Presidio or vi_core_news_lg is not installed."""

    PATTERNS = {
        "VN_CCCD": re.compile(r"(?<!\d)\d{11,12}(?!\d)"),
        "VN_PHONE": re.compile(r"(?<!\d)(?:0[35789]\d{8}|[35789]\d{8})(?!\d)"),
        "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "PERSON": re.compile(r"\b[^\W\d_]+(?:\s+[^\W\d_]+){1,5}\b", re.UNICODE),
    }

    def analyze(self, text: str, language: str = "vi", entities: list | None = None, **kwargs) -> list:
        del language, kwargs
        wanted = set(entities or self.PATTERNS.keys())
        results = []
        for entity_type, pattern in self.PATTERNS.items():
            if entity_type not in wanted:
                continue
            for match in pattern.finditer(str(text)):
                results.append(SimpleRecognizerResult(entity_type, match.start(), match.end(), 0.85))
        return results


def build_vietnamese_analyzer():
    """Build a Vietnamese PII analyzer with custom CCCD, phone, email and name recognizers."""
    if AnalyzerEngine is None:
        return RegexVietnameseAnalyzer()

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[Pattern(name="cccd_pattern", regex=r"(?<!\d)\d{11,12}(?!\d)", score=0.9)],
        context=["cccd", "can cuoc", "chung minh", "cmnd"],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[
            Pattern(
                name="vn_phone",
                regex=r"(?<!\d)(?:0[35789]\d{8}|[35789]\d{8})(?!\d)",
                score=0.85,
            )
        ],
        context=["dien thoai", "sdt", "phone", "lien he"],
    )
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[
            Pattern(
                name="email",
                regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                score=0.9,
            )
        ],
        context=["email", "mail"],
    )
    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[
            Pattern(
                name="vn_person_name",
                regex=r"\b[^\W\d_]+(?:\s+[^\W\d_]+){1,5}\b",
                score=0.7,
            )
        ],
        context=["benh nhan", "ho_ten", "bac si", "bac_si"],
    )

    try:
        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "vi", "model_name": "vi_core_news_lg"}],
            }
        )
        nlp_engine = provider.create_engine()
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["vi"])
    except Exception:
        return RegexVietnameseAnalyzer()

    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)
    return analyzer


def detect_pii(text: str, analyzer) -> list:
    """Detect PERSON, EMAIL_ADDRESS, VN_CCCD and VN_PHONE in Vietnamese text."""
    return analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )

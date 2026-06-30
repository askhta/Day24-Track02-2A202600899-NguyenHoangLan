# src/pii/anonymizer.py
import hashlib
import secrets

import pandas as pd
from faker import Faker

try:
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
except ImportError:
    AnonymizerEngine = None
    OperatorConfig = None

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def fake_cccd() -> str:
    return str(secrets.randbelow(9) + 1) + "".join(str(secrets.randbelow(10)) for _ in range(11))


def fake_vn_phone() -> str:
    return "0" + secrets.choice(["3", "5", "7", "8", "9"]) + "".join(
        str(secrets.randbelow(10)) for _ in range(8)
    )


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine() if AnonymizerEngine else None

    def _replacement_for(self, entity_type: str, original: str, strategy: str) -> str:
        if strategy == "hash":
            return hashlib.sha256(original.encode("utf-8")).hexdigest()
        if strategy == "mask":
            visible = 1 if len(original) <= 4 else 2
            return original[:visible] + "*" * max(len(original) - visible, 0)
        replacements = {
            "PERSON": fake.name(),
            "EMAIL_ADDRESS": fake.email(),
            "VN_CCCD": fake_cccd(),
            "VN_PHONE": fake_vn_phone(),
        }
        return replacements.get(entity_type, "<ANONYMIZED>")

    def _manual_anonymize(self, text: str, results: list, strategy: str) -> str:
        anonymized = str(text)
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original = anonymized[result.start:result.end]
            replacement = self._replacement_for(result.entity_type, original, strategy)
            anonymized = anonymized[:result.start] + replacement + anonymized[result.end:]
        return anonymized

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        results = detect_pii(str(text), self.analyzer)
        if not results:
            return str(text)

        if self.anonymizer is None or OperatorConfig is None:
            return self._manual_anonymize(str(text), results, strategy)

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": fake_vn_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "DEFAULT": OperatorConfig(
                    "mask",
                    {"type": "mask", "masking_char": "*", "chars_to_mask": 100, "from_end": True},
                )
            }
        elif strategy == "hash":
            operators = {"DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})}
        else:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")

        anonymized = self.anonymizer.anonymize(
            text=str(text),
            analyzer_results=results,
            operators=operators,
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_anon = df.copy()

        if "ho_ten" in df_anon:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "bac_si_phu_trach" in df_anon:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "email" in df_anon:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon:
            df_anon["dia_chi"] = [fake.address().replace("\n", ", ") for _ in range(len(df_anon))]
        if "cccd" in df_anon:
            df_anon["cccd"] = [fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon:
            df_anon["so_dien_thoai"] = [fake_vn_phone() for _ in range(len(df_anon))]

        return df_anon

    def calculate_detection_rate(self, original_df: pd.DataFrame, pii_columns: list) -> float:
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0

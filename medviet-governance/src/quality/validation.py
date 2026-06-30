# src/quality/validation.py
import re
from pathlib import Path

import pandas as pd

try:
    import great_expectations as gx
    from great_expectations.core.expectation_suite import ExpectationSuite
except ImportError:
    gx = None
    ExpectationSuite = object

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "patients_raw.csv"


def build_patient_expectation_suite() -> ExpectationSuite:
    if gx is None:
        raise ImportError("great_expectations is required to build the expectation suite")

    context = gx.get_context()
    suite_name = "patient_data_suite"
    try:
        suite = context.add_expectation_suite(suite_name)
    except Exception:
        suite = context.get_expectation_suite(suite_name)

    df = pd.read_csv(RAW_DATA_PATH)
    validator = context.sources.pandas_default.read_dataframe(df)

    validator.expect_column_values_to_not_be_null("patient_id")
    validator.expect_column_value_lengths_to_equal(column="cccd", value=12)
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50,
    )
    valid_conditions = [
        "Tieu duong",
        "Huyet ap cao",
        "Tim mach",
        "Khoe manh",
        "Tiá»ƒu Ä‘Æ°á»ng",
        "Huyáº¿t Ã¡p cao",
        "Tim máº¡ch",
        "Khá»e máº¡nh",
    ]
    validator.expect_column_values_to_be_in_set(column="benh", value_set=valid_conditions)
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
    )
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def _fail(results: dict, check_name: str) -> None:
    results["success"] = False
    results["failed_checks"].append(check_name)


def validate_anonymized_data(filepath: str) -> dict:
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
        },
    }

    if "cccd" in df.columns:
        raw_cccd = set()
        if RAW_DATA_PATH.exists():
            raw_cccd = set(pd.read_csv(RAW_DATA_PATH)["cccd"].astype(str))
        anon_cccd = set(df["cccd"].astype(str))
        if raw_cccd and raw_cccd.intersection(anon_cccd):
            _fail(results, "cccd_contains_original_values")
        if not df["cccd"].astype(str).str.match(r"^\d{12}$").all():
            _fail(results, "cccd_invalid_format")

    important_columns = ["patient_id", "cccd", "so_dien_thoai", "email", "benh", "ket_qua_xet_nghiem"]
    missing_or_null = [
        col for col in important_columns if col not in df.columns or df[col].isna().any()
    ]
    if missing_or_null:
        results["stats"]["missing_or_null_columns"] = missing_or_null
        _fail(results, "important_columns_not_null")

    if RAW_DATA_PATH.exists() and len(df) != len(pd.read_csv(RAW_DATA_PATH)):
        _fail(results, "row_count_matches_raw")

    if "email" in df.columns and not df["email"].astype(str).str.match(
        re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    ).all():
        _fail(results, "email_invalid_format")

    return results

"""Medical report parser for PDF, text, and structured input."""

import re
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


TEST_NAME_ALIASES = {
    # Hemoglobin
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    "haemoglobin": "hemoglobin",
    # White blood cells
    "wbc": "white_blood_cells",
    "leukocytes": "white_blood_cells",
    "white blood cells": "white_blood_cells",
    "white blood count": "white_blood_cells",
    # Platelets
    "plt": "platelets",
    "thrombocytes": "platelets",
    # Red blood cells
    "rbc": "red_blood_cells",
    "erythrocytes": "red_blood_cells",
    "red blood cells": "red_blood_cells",
    # MCV
    "mcv": "mean_corpuscular_volume",
    "mean corpuscular volume": "mean_corpuscular_volume",
    # Glucose
    "fbs": "glucose_fasting",
    "fpg": "glucose_fasting",
    "fasting glucose": "glucose_fasting",
    "fasting blood sugar": "glucose_fasting",
    "fasting blood glucose": "glucose_fasting",
    # Creatinine
    "cr": "creatinine",
    "creat": "creatinine",
    "serum creatinine": "creatinine",
    # BUN
    "bun": "blood_urea_nitrogen",
    "urea nitrogen": "blood_urea_nitrogen",
    "blood urea nitrogen": "blood_urea_nitrogen",
    # Liver enzymes
    "sgpt": "alt",
    "alanine aminotransferase": "alt",
    "alanine transaminase": "alt",
    "sgot": "ast",
    "aspartate aminotransferase": "ast",
    "aspartate transaminase": "ast",
    # HbA1c
    "hba1c": "hba1c",
    "a1c": "hba1c",
    "glycated hemoglobin": "hba1c",
    "glycohemoglobin": "hba1c",
    # Cholesterol
    "cholesterol": "total_cholesterol",
    "total cholesterol": "total_cholesterol",
    "ldl": "ldl_cholesterol",
    "low density lipoprotein": "ldl_cholesterol",
    "tg": "triglycerides",
    "trigs": "triglycerides",
    # Thyroid
    "thyroid stimulating hormone": "tsh",
    "thyrotropin": "tsh",
    "thyroxine": "free_t4",
    "ft4": "free_t4",
    # Urine tests
    "urine protein": "urine_protein",
    "proteinuria": "urine_protein",
    "urine glucose": "urine_glucose",
    "glucosuria": "urine_glucose",
    "urine blood": "urine_blood",
    "hematuria": "urine_blood",
    "urine ph": "urine_ph",
    "urine specific gravity": "urine_specific_gravity",
    "sg": "urine_specific_gravity",
    "urine ketones": "urine_ketones",
    "ketonuria": "urine_ketones",
    "leukocyte esterase": "leukocyte_esterase",
    "wbc esterase": "leukocyte_esterase",
    "urine nitrites": "urine_nitrites",
    "nitrites": "urine_nitrites",
    # Stool tests
    "fobt": "fecal_occult_blood",
    "occult blood": "fecal_occult_blood",
    "fecal occult blood": "fecal_occult_blood",
    "stool ph": "stool_ph",
    "fecal fat": "fecal_fat",
    "stool fat": "fecal_fat",
    "calprotectin": "fecal_calprotectin",
    "fecal calprotectin": "fecal_calprotectin",
    "stool wbc": "stool_white_blood_cells",
    "fecal wbc": "stool_white_blood_cells",
    "stool culture": "stool_culture",
    "ova and parasites": "ova_and_parasites",
    "o&p": "ova_and_parasites",
}

QUALITATIVE_VALUES = {
    "positive", "negative", "trace", "present", "absent",
    "none", "no_pathogens", "1+", "2+", "3+", "4+"
}


class MedicalReportParser:
    """Parser for medical laboratory reports."""

    def parse_pdf(self, pdf_path: str) -> list[dict]:
        """Parse a PDF medical report."""
        text = self._extract_text_from_pdf(pdf_path)
        return self.parse_text(text)

    def parse_text(self, text: str) -> list[dict]:
        """Parse plain text medical report."""
        results = []
        if not text:
            return results
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = self._parse_line(line)
            if parsed:
                results.append(parsed)
        return results

    def parse_structured_input(self, test_data: dict) -> list[dict]:
        """Parse structured form input (dict of test_name -> value)."""
        results = []
        for raw_name, value in test_data.items():
            if value is None or value == "":
                continue
            std_name = self._standardize_test_name(raw_name)
            if std_name is None:
                continue
            is_qualitative = isinstance(value, str) and value.lower() in QUALITATIVE_VALUES
            if is_qualitative:
                results.append({
                    "test_name": std_name,
                    "original_name": raw_name,
                    "value": value.lower(),
                    "unit": None,
                    "is_qualitative": True,
                })
            else:
                num_val = self._parse_number(str(value))
                if num_val is not None:
                    results.append({
                        "test_name": std_name,
                        "original_name": raw_name,
                        "value": num_val,
                        "unit": None,
                        "is_qualitative": False,
                    })
        return results

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        if pdfplumber is None:
            raise ImportError("pdfplumber is required for PDF parsing")
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Try table extraction first
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text_parts.append(" | ".join(str(c) if c else "" for c in row))
                # Also get raw text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    def _parse_line(self, line: str) -> Optional[dict]:
        """Parse a single line from a report."""
        # Pattern: Test: value unit  OR  Test = value unit
        colon_pattern = re.compile(
            r'^([A-Za-z][A-Za-z0-9\s\(\)/\-_]+?)\s*[:=]\s*'
            r'([0-9]+\.?[0-9]*|[A-Za-z+]+)\s*([A-Za-z/%μ\^0-9]*)?$'
        )
        # Pattern: Test | value | unit
        pipe_pattern = re.compile(
            r'^([A-Za-z][A-Za-z0-9\s\(\)/\-_]+?)\s*\|\s*'
            r'([0-9]+\.?[0-9]*|[A-Za-z+]+)\s*\|\s*([A-Za-z/%μ\^0-9]*)?$'
        )

        match = colon_pattern.match(line) or pipe_pattern.match(line)
        if not match:
            return None

        raw_name = match.group(1).strip()
        raw_value = match.group(2).strip()
        unit = match.group(3).strip() if match.group(3) else None

        std_name = self._standardize_test_name(raw_name)
        if std_name is None:
            return None

        is_qualitative = raw_value.lower() in QUALITATIVE_VALUES
        if is_qualitative:
            return {
                "test_name": std_name,
                "original_name": raw_name,
                "value": raw_value.lower(),
                "unit": unit or None,
                "is_qualitative": True,
            }
        else:
            num_val = self._parse_number(raw_value)
            if num_val is None:
                return None
            return {
                "test_name": std_name,
                "original_name": raw_name,
                "value": num_val,
                "unit": unit or None,
                "is_qualitative": False,
            }

    def _standardize_test_name(self, name: str) -> Optional[str]:
        """Convert test name to standardized form."""
        lower = name.lower().strip()
        # Direct match
        if lower in TEST_NAME_ALIASES:
            return TEST_NAME_ALIASES[lower]
        # Check if it's already a canonical name
        canonical_names = set(TEST_NAME_ALIASES.values())
        if lower in canonical_names or lower.replace(" ", "_") in canonical_names:
            return lower.replace(" ", "_")
        return None

    def _parse_number(self, value: str) -> Optional[float]:
        """Parse a numeric value from string."""
        try:
            return float(value.replace(",", ""))
        except (ValueError, AttributeError):
            return None

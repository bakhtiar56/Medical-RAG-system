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
    "hemoglobin": "hemoglobin",
    # White blood cells
    "wbc": "white_blood_cells",
    "leukocytes": "white_blood_cells",
    "white blood cells": "white_blood_cells",
    "white blood count": "white_blood_cells",
    "wbc count": "white_blood_cells",
    # Platelets
    "plt": "platelets",
    "thrombocytes": "platelets",
    "platelet count": "platelets",
    # Red blood cells
    "rbc": "red_blood_cells",
    "erythrocytes": "red_blood_cells",
    "red blood cells": "red_blood_cells",
    "rbc count": "red_blood_cells",
    # MCV
    "mcv": "mean_corpuscular_volume",
    "mean corpuscular volume": "mean_corpuscular_volume",
    # MCH / MCHC / RDW / MPV
    "mch": "mch",
    "mchc": "mchc",
    "rdw": "rdw",
    "rdw cv": "rdw",
    "mpv": "mpv",
    # Hematocrit
    "hematocrit": "hematocrit",
    "hct": "hematocrit",
    "pcv": "hematocrit",
    # ESR
    "esr": "esr",
    "erythrocyte sedimentation rate": "esr",
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
    "creatinine, serum": "creatinine",
    "creatinine serum": "creatinine",
    "creatinine": "creatinine",
    # BUN / Urea
    "bun": "blood_urea_nitrogen",
    "urea nitrogen": "blood_urea_nitrogen",
    "blood urea nitrogen": "blood_urea_nitrogen",
    "urea": "blood_urea_nitrogen",
    # Uric acid
    "uric acid": "uric_acid",
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
    "direct ldl": "ldl_cholesterol",
    "ldl cholesterol": "ldl_cholesterol",
    "tg": "triglycerides",
    "trigs": "triglycerides",
    "triglyceride": "triglycerides",
    "triglycerides": "triglycerides",
    "hdl cholesterol": "hdl_cholesterol",
    "hdl": "hdl_cholesterol",
    "vldl": "vldl_cholesterol",
    "vldl cholesterol": "vldl_cholesterol",
    # Thyroid
    "thyroid stimulating hormone": "tsh",
    "thyrotropin": "tsh",
    "tsh": "tsh",
    "tsh - thyroid stimulating hormone": "tsh",
    "thyroxine": "free_t4",
    "ft4": "free_t4",
    "t4": "free_t4",
    "t4 - thyroxine": "free_t4",
    "t3": "t3",
    "t3 - triiodothyronine": "t3",
    "triiodothyronine": "t3",
    # Vitamins
    "25(oh) vitamin d": "vitamin_d",
    "vitamin d": "vitamin_d",
    "25-oh vitamin d": "vitamin_d",
    "vitamin b12": "vitamin_b12",
    "b12": "vitamin_b12",
    "cobalamin": "vitamin_b12",
    # Homocysteine
    "homocysteine": "homocysteine",
    "homocysteine, serum": "homocysteine",
    # Proteins / Liver panel
    "total protein": "total_protein",
    "albumin": "albumin",
    "globulin": "globulin",
    "a/g ratio": "ag_ratio",
    # Bilirubin
    "total bilirubin": "total_bilirubin",
    "bilirubin total": "total_bilirubin",
    "conjugated bilirubin": "conjugated_bilirubin",
    "direct bilirubin": "conjugated_bilirubin",
    "unconjugated bilirubin": "unconjugated_bilirubin",
    # Iron studies
    "iron": "iron",
    "serum iron": "iron",
    "total iron binding capacity": "tibc",
    "total iron binding capacity (tibc)": "tibc",
    "tibc": "tibc",
    "transferrin saturation": "transferrin_saturation",
    # Electrolytes
    "sodium": "sodium",
    "sodium (na+)": "sodium",
    "na+": "sodium",
    "na": "sodium",
    "potassium": "potassium",
    "potassium (k+)": "potassium",
    "k+": "potassium",
    "k": "potassium",
    "chloride": "chloride",
    "chloride (cl-)": "chloride",
    "cl-": "chloride",
    "cl": "chloride",
    "calcium": "calcium",
    "ca": "calcium",
    # Immunology
    "ige": "ige",
    "immunoglobulin e": "ige",
    "psa": "psa",
    "prostate specific antigen": "psa",
    "psa-prostate specific antigen, total": "psa",
    # Hepatitis
    "hbsag": "hbsag",
    # Mean blood glucose
    "mean blood glucose": "mean_blood_glucose",
    # Urine tests
    "urine protein": "urine_protein",
    "proteinuria": "urine_protein",
    "urine glucose": "urine_glucose",
    "glucosuria": "urine_glucose",
    "urine blood": "urine_blood",
    "hematuria": "urine_blood",
    "urine ph": "urine_ph",
    "ph": "urine_ph",
    "urine specific gravity": "urine_specific_gravity",
    "sg": "urine_specific_gravity",
    "specific gravity": "urine_specific_gravity",
    "urine ketones": "urine_ketones",
    "urine ketone": "urine_ketones",
    "ketonuria": "urine_ketones",
    "leukocyte esterase": "leukocyte_esterase",
    "wbc esterase": "leukocyte_esterase",
    "urine nitrites": "urine_nitrites",
    "nitrites": "urine_nitrites",
    "nitrite": "urine_nitrites",
    "microalbumin": "microalbumin",
    "microalbumin (per urine volume)": "microalbumin",
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
    "none", "no_pathogens", "1+", "2+", "3+", "4+",
    "reactive", "non reactive", "non-reactive",
    "detected", "not detected",
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
        if match:
            raw_name = match.group(1).strip()
            raw_value = match.group(2).strip()
            unit = match.group(3).strip() if match.group(3) else None

            std_name = self._standardize_test_name(raw_name)
            if std_name is not None:
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
                    if num_val is not None:
                        return {
                            "test_name": std_name,
                            "original_name": raw_name,
                            "value": num_val,
                            "unit": unit or None,
                            "is_qualitative": False,
                        }

        # Fallback: try lab report format (result is last number on line)
        return self._parse_lab_report_line(line)

    def _parse_lab_report_line(self, line: str) -> Optional[dict]:
        """Parse lab report lines where the result is the last number on the line.

        Handles formats like:
            Hemoglobin g/dL 13.0 - 16.5Colorimetric 14.5
            WBC Count H /cmm 4000 - 10000SF Cube cell analysis 10570
            Creatinine, Serum mg/dL 0.66 - 1.25 Creatinine Amidohydrolase 0.83
            Urine Glucose Absent GOD-POD Present (+)
        """
        # Skip header/footer/metadata lines
        skip_patterns = [
            r'(?i)^(dr\.|page |this is|sample |patient |ref\.|printed|registration|collected|approved|lab id|scan qr|passport|location|sex/age|status)',
            r'(?i)^(test result|biological ref|differential count|absolute count|interpretation|explanation|reference|limitations|summary)',
            r'(?i)^(complete blood count|lipid profile|biochemistry|thyroid function|iron studies|immunoassay|protein|bilirubin|electrolytes|hb electrophoresis)',
            r'(?i)^(physical & chemical|microscopic examination|peripheral smear)',
            r'(?i)(end of report|laboratory test report|client name|sterling accuris)',
            r'^\d{2,}[-/]\d',  # Dates
            r'^[A-Z]{2,}-\d{4}',  # Report/machine IDs
        ]
        for skip in skip_patterns:
            if re.search(skip, line):
                return None

        # Try to find a known test name at the start of the line
        # Sort aliases by length (longest first) so we match the most specific name
        line_lower = line.lower().strip()

        # Build list of all known names (aliases + canonical) sorted longest first
        all_names = list(TEST_NAME_ALIASES.keys())
        canonical = set(TEST_NAME_ALIASES.values())
        for c in canonical:
            readable = c.replace('_', ' ')
            if readable not in all_names:
                all_names.append(readable)
        all_names.sort(key=len, reverse=True)

        matched_name = None
        matched_std = None
        rest_of_line = ""

        for name in all_names:
            if line_lower.startswith(name):
                # Check that the match ends at a word boundary
                end_pos = len(name)
                if end_pos < len(line_lower) and line_lower[end_pos].isalpha():
                    continue
                matched_name = line[:end_pos].strip()
                matched_std = self._standardize_test_name(name)
                rest_of_line = line[end_pos:].strip()
                break

        # Also try with H/L flag stripped from the test name area
        if not matched_name:
            for name in all_names:
                pattern = re.compile(re.escape(name) + r'\s+[HL]\b', re.IGNORECASE)
                m = pattern.match(line_lower)
                if m:
                    matched_name = line[:m.end()].strip()
                    matched_std = self._standardize_test_name(name)
                    rest_of_line = line[m.end():].strip()
                    break

        if not matched_name or not matched_std:
            return None

        # Check for qualitative values - look at the last word(s) on the line
        last_tokens = rest_of_line.split()
        if last_tokens:
            last_word = last_tokens[-1].strip('()').lower()
            last_two = ' '.join(last_tokens[-2:]).lower() if len(last_tokens) >= 2 else ''

            qual_check = last_word
            if qual_check in QUALITATIVE_VALUES:
                value = qual_check
                if last_two.startswith('non '):
                    value = 'negative'
                elif qual_check == 'reactive':
                    value = 'positive'
                elif qual_check == 'detected':
                    value = 'positive'
                elif qual_check in ('not detected', 'not_detected'):
                    value = 'negative'
                elif qual_check == 'present':
                    value = 'present'
                return {
                    "test_name": matched_std,
                    "original_name": matched_name,
                    "value": value,
                    "unit": None,
                    "is_qualitative": True,
                }

        # Extract the last number on the line as the result value
        numbers = re.findall(r'(?<![<>])(\d+(?:\.\d+)?)', rest_of_line)
        if not numbers:
            # Try with < or > prefix (e.g., "< 148")
            prefixed = re.findall(r'[<>]\s*(\d+(?:\.\d+)?)', rest_of_line)
            if prefixed:
                numbers = prefixed

        if numbers:
            result_value = self._parse_number(numbers[-1])
            if result_value is not None:
                return {
                    "test_name": matched_std,
                    "original_name": matched_name,
                    "value": result_value,
                    "unit": None,
                    "is_qualitative": False,
                }

        return None

    def _standardize_test_name(self, name: str) -> Optional[str]:
        """Convert test name to standardized form."""
        lower = name.lower().strip()
        # Direct match
        if lower in TEST_NAME_ALIASES:
            return TEST_NAME_ALIASES[lower]
        # Strip trailing H or L flags (e.g., "WBC Count H" -> "WBC Count")
        stripped = re.sub(r'\s+[HL]$', '', lower)
        if stripped in TEST_NAME_ALIASES:
            return TEST_NAME_ALIASES[stripped]
        # Try without comma suffix (e.g., "Creatinine, Serum" -> "creatinine")
        if ',' in lower:
            before_comma = lower.split(',')[0].strip()
            if before_comma in TEST_NAME_ALIASES:
                return TEST_NAME_ALIASES[before_comma]
        # Check if it's already a canonical name
        canonical_names = set(TEST_NAME_ALIASES.values())
        if lower in canonical_names or lower.replace(" ", "_") in canonical_names:
            return lower.replace(" ", "_")
        if stripped in canonical_names or stripped.replace(" ", "_") in canonical_names:
            return stripped.replace(" ", "_")
        return None

    def _parse_number(self, value: str) -> Optional[float]:
        """Parse a numeric value from string."""
        try:
            return float(value.replace(",", ""))
        except (ValueError, AttributeError):
            return None

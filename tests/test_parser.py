"""Tests for medical report parser."""
import pytest
from src.report_parser import MedicalReportParser


class TestTextParsing:
    def setup_method(self):
        self.parser = MedicalReportParser()

    def test_parse_standard_format(self):
        text = "Hemoglobin: 12.5 g/dL"
        results = self.parser.parse_text(text)
        assert len(results) == 1
        assert results[0]["test_name"] == "hemoglobin"
        assert results[0]["value"] == 12.5
        assert results[0]["is_qualitative"] is False

    def test_parse_qualitative_values(self):
        text = "Urine Blood: Positive"
        results = self.parser.parse_text(text)
        assert len(results) == 1
        assert results[0]["test_name"] == "urine_blood"
        assert results[0]["value"] == "positive"
        assert results[0]["is_qualitative"] is True

    def test_parse_pipe_separated_format(self):
        text = "WBC | 8500 | cells/μL"
        results = self.parser.parse_text(text)
        assert len(results) == 1
        assert results[0]["test_name"] == "white_blood_cells"
        assert results[0]["value"] == 8500.0

    def test_parse_aliases(self):
        text = "HGB: 13.0 g/dL"
        results = self.parser.parse_text(text)
        assert len(results) == 1
        assert results[0]["test_name"] == "hemoglobin"

    def test_parse_empty_text(self):
        results = self.parser.parse_text("")
        assert results == []

    def test_parse_unrecognized_tests(self):
        text = "SomeUnknownTest: 99.9 units"
        results = self.parser.parse_text(text)
        assert results == []


class TestStructuredInput:
    def setup_method(self):
        self.parser = MedicalReportParser()

    def test_parse_form_data(self):
        data = {
            "hemoglobin": 11.0,
            "glucose_fasting": 180.0,
            "urine_blood": "positive",
        }
        results = self.parser.parse_structured_input(data)
        assert len(results) == 3
        names = {r["test_name"] for r in results}
        assert "hemoglobin" in names
        assert "glucose_fasting" in names
        assert "urine_blood" in names

    def test_parse_empty_form(self):
        results = self.parser.parse_structured_input({})
        assert results == []

    def test_parse_form_with_unknown_tests(self):
        data = {"unknown_test": 42.0, "hemoglobin": 13.0}
        results = self.parser.parse_structured_input(data)
        assert len(results) == 1
        assert results[0]["test_name"] == "hemoglobin"


class TestNameStandardization:
    def setup_method(self):
        self.parser = MedicalReportParser()

    def test_direct_aliases(self):
        assert self.parser._standardize_test_name("hgb") == "hemoglobin"
        assert self.parser._standardize_test_name("sgpt") == "alt"
        assert self.parser._standardize_test_name("fbs") == "glucose_fasting"
        assert self.parser._standardize_test_name("fobt") == "fecal_occult_blood"
        assert self.parser._standardize_test_name("wbc") == "white_blood_cells"

    def test_unknown_test_returns_none(self):
        assert self.parser._standardize_test_name("totally_unknown_xyz") is None

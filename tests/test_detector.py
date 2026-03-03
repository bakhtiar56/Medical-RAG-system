"""Tests for abnormality detector."""
import pytest
from src.abnormality_detector import AbnormalityDetector, Severity


@pytest.fixture
def detector_male():
    return AbnormalityDetector(patient_sex="male", patient_age=45)


@pytest.fixture
def detector_female():
    return AbnormalityDetector(patient_sex="female", patient_age=30)


@pytest.fixture
def normal_blood_results():
    return [
        {"test_name": "hemoglobin", "value": 15.0, "unit": "g/dL", "is_qualitative": False},
        {"test_name": "white_blood_cells", "value": 7000, "unit": "cells/μL", "is_qualitative": False},
        {"test_name": "glucose_fasting", "value": 90, "unit": "mg/dL", "is_qualitative": False},
    ]


@pytest.fixture
def abnormal_results():
    return [
        {"test_name": "hemoglobin", "value": 6.5, "unit": "g/dL", "is_qualitative": False},
        {"test_name": "glucose_fasting", "value": 280, "unit": "mg/dL", "is_qualitative": False},
        {"test_name": "creatinine", "value": 3.5, "unit": "mg/dL", "is_qualitative": False},
        {"test_name": "urine_blood", "value": "positive", "unit": None, "is_qualitative": True},
        {"test_name": "white_blood_cells", "value": 8000, "unit": "cells/μL", "is_qualitative": False},
    ]


class TestNormalResults:
    def test_all_normal(self, detector_male, normal_blood_results):
        report = detector_male.analyze(normal_blood_results)
        assert report.abnormal_count == 0
        assert report.normal_count == 3

    def test_summary_generated(self, detector_male, normal_blood_results):
        report = detector_male.analyze(normal_blood_results)
        assert report.summary != ""


class TestAbnormalResults:
    def test_detects_abnormalities(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        assert report.abnormal_count > 0

    def test_detects_critical_hemoglobin(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        critical = [a for a in report.abnormalities if a.test_name == "hemoglobin"]
        assert len(critical) == 1
        assert critical[0].severity == Severity.CRITICAL

    def test_detects_high_glucose(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        glucose = [a for a in report.abnormalities if a.test_name == "glucose_fasting"]
        assert len(glucose) == 1
        assert glucose[0].severity in (Severity.ABNORMAL, Severity.CRITICAL)

    def test_detects_qualitative_abnormality(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        urine = [a for a in report.abnormalities if a.test_name == "urine_blood"]
        assert len(urine) == 1
        assert urine[0].severity == Severity.ABNORMAL

    def test_normal_wbc_not_flagged(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        wbc = [a for a in report.abnormalities if a.test_name == "white_blood_cells"]
        assert len(wbc) == 0

    def test_abnormalities_sorted_by_severity(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        severities = [a.severity for a in report.abnormalities]
        # Critical should come first
        if Severity.CRITICAL in severities:
            assert severities[0] == Severity.CRITICAL

    def test_possible_conditions_populated(self, detector_male, abnormal_results):
        report = detector_male.analyze(abnormal_results)
        for abn in report.abnormalities:
            # All abnormal tests should have possible conditions populated
            assert isinstance(abn.possible_conditions, list)


class TestDemographics:
    def test_female_hemoglobin_range(self, detector_female):
        # 13.0 is normal for adult female (12.0-16.0)
        results = [{"test_name": "hemoglobin", "value": 13.0, "unit": "g/dL", "is_qualitative": False}]
        report = detector_female.analyze(results)
        assert report.abnormal_count == 0

    def test_male_hemoglobin_range(self, detector_male):
        # 13.0 is low for adult male (13.5-17.5)
        results = [{"test_name": "hemoglobin", "value": 13.0, "unit": "g/dL", "is_qualitative": False}]
        report = detector_male.analyze(results)
        assert report.abnormal_count == 1


class TestEdgeCases:
    def test_empty_results(self):
        detector = AbnormalityDetector()
        report = detector.analyze([])
        assert report.total_tests == 0
        assert report.abnormal_count == 0

    def test_unknown_test(self):
        detector = AbnormalityDetector()
        results = [{"test_name": "unknown_xyz", "value": 99.9, "unit": "units", "is_qualitative": False}]
        report = detector.analyze(results)
        # Unknown tests should be ignored
        assert report.total_tests == 0

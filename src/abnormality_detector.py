"""Abnormality detection module for medical lab results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.knowledge_builder import MedicalKnowledgeBase


class Severity(Enum):
    NORMAL = "normal"
    BORDERLINE = "borderline"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"


@dataclass
class TestAbnormality:
    test_name: str
    value: object
    unit: Optional[str]
    severity: Severity
    direction: Optional[str]  # "low", "high", or None for qualitative
    deviation_pct: Optional[float]
    normal_range: Optional[dict]
    possible_conditions: list[str] = field(default_factory=list)
    is_qualitative: bool = False
    message: str = ""


@dataclass
class DetectionReport:
    total_tests: int
    normal_count: int
    abnormal_count: int
    critical_count: int
    abnormalities: list[TestAbnormality]
    summary: str = ""


class AbnormalityDetector:
    """Detects abnormal values in lab results."""

    BORDERLINE_MARGIN = 0.10  # 10% from boundary

    def __init__(self, patient_sex: str = "adult", patient_age: int = 35):
        self.kb = MedicalKnowledgeBase()
        self.patient_sex = patient_sex.lower()
        self.patient_age = patient_age
        self._demo_key = self._resolve_demographic()

    def _resolve_demographic(self) -> str:
        if self.patient_age < 18:
            return "child"
        if self.patient_sex in ("male", "m"):
            return "adult_male"
        if self.patient_sex in ("female", "f"):
            return "adult_female"
        return "adult"

    def analyze(self, parsed_results: list[dict]) -> DetectionReport:
        """Analyze parsed lab results and return detection report."""
        abnormalities = []
        normal_count = 0

        for result in parsed_results:
            test_name = result["test_name"]
            test_info = self.kb.get_test_info(test_name)
            if test_info is None:
                continue

            if result.get("is_qualitative"):
                abn = self._evaluate_qualitative(result, test_info)
            else:
                abn = self._evaluate_quantitative(result, test_info)

            if abn.severity == Severity.NORMAL:
                normal_count += 1
            else:
                abnormalities.append(abn)

        # Sort: critical first, then abnormal, then borderline
        severity_order = {Severity.CRITICAL: 0, Severity.ABNORMAL: 1, Severity.BORDERLINE: 2}
        abnormalities.sort(key=lambda a: severity_order.get(a.severity, 3))

        critical_count = sum(1 for a in abnormalities if a.severity == Severity.CRITICAL)
        abnormal_count = len(abnormalities)
        total = normal_count + abnormal_count

        report = DetectionReport(
            total_tests=total,
            normal_count=normal_count,
            abnormal_count=abnormal_count,
            critical_count=critical_count,
            abnormalities=abnormalities,
        )
        report.summary = self._generate_summary(report)
        return report

    def _evaluate_quantitative(self, result: dict, test_info: dict) -> TestAbnormality:
        value = result["value"]
        test_name = result["test_name"]
        unit = result.get("unit") or test_info.get("unit")

        # Check critical values first
        critical = self.kb.get_critical_value(test_name)
        if critical:
            if critical.get("low") is not None and value <= critical["low"]:
                return TestAbnormality(
                    test_name=test_name, value=value, unit=unit,
                    severity=Severity.CRITICAL, direction="low",
                    deviation_pct=None, normal_range=None,
                    possible_conditions=test_info.get("low_conditions", []),
                    message=critical.get("action_low", "CRITICAL: Dangerously low value"),
                )
            if critical.get("high") is not None and value >= critical["high"]:
                return TestAbnormality(
                    test_name=test_name, value=value, unit=unit,
                    severity=Severity.CRITICAL, direction="high",
                    deviation_pct=None, normal_range=None,
                    possible_conditions=test_info.get("high_conditions", []),
                    message=critical.get("action_high", "CRITICAL: Dangerously high value"),
                )

        # Get applicable normal range
        normal_range = self._get_applicable_range(test_info)
        if normal_range is None:
            return TestAbnormality(
                test_name=test_name, value=value, unit=unit,
                severity=Severity.NORMAL, direction=None,
                deviation_pct=None, normal_range=None,
            )

        low, high = normal_range.get("min"), normal_range.get("max")

        if low is not None and value < low:
            dev = (low - value) / low * 100 if low != 0 else 0
            sev = Severity.BORDERLINE if dev <= self.BORDERLINE_MARGIN * 100 else Severity.ABNORMAL
            return TestAbnormality(
                test_name=test_name, value=value, unit=unit,
                severity=sev, direction="low",
                deviation_pct=round(dev, 1), normal_range=normal_range,
                possible_conditions=test_info.get("low_conditions", []),
                message=f"Below normal range ({low}-{high} {unit or ''})",
            )
        if high is not None and value > high:
            dev = (value - high) / high * 100 if high != 0 else 0
            sev = Severity.BORDERLINE if dev <= self.BORDERLINE_MARGIN * 100 else Severity.ABNORMAL
            return TestAbnormality(
                test_name=test_name, value=value, unit=unit,
                severity=sev, direction="high",
                deviation_pct=round(dev, 1), normal_range=normal_range,
                possible_conditions=test_info.get("high_conditions", []),
                message=f"Above normal range ({low}-{high} {unit or ''})",
            )

        return TestAbnormality(
            test_name=test_name, value=value, unit=unit,
            severity=Severity.NORMAL, direction=None,
            deviation_pct=0.0, normal_range=normal_range,
        )

    def _evaluate_qualitative(self, result: dict, test_info: dict) -> TestAbnormality:
        value = result["value"]
        test_name = result["test_name"]
        normal_value = test_info.get("normal_value", "negative")
        is_abnormal = str(value).lower() != str(normal_value).lower()

        if is_abnormal:
            conditions = test_info.get("abnormal_conditions", [])
            return TestAbnormality(
                test_name=test_name, value=value, unit=None,
                severity=Severity.ABNORMAL, direction=None,
                deviation_pct=None, normal_range=None,
                possible_conditions=conditions,
                is_qualitative=True,
                message=f"Abnormal result: {value} (expected {normal_value})",
            )
        return TestAbnormality(
            test_name=test_name, value=value, unit=None,
            severity=Severity.NORMAL, direction=None,
            deviation_pct=None, normal_range=None,
            is_qualitative=True,
        )

    def _get_applicable_range(self, test_info: dict) -> Optional[dict]:
        """Get the most specific normal range for patient demographics."""
        ranges = test_info.get("normal_ranges", {})
        if not ranges:
            return None

        # Try specific demographic first, then fall back
        fallback_order = [self._demo_key, "adult", "adult_male", "adult_female", "child"]
        # Also handle adult_male -> adult fallback
        if self._demo_key == "adult_male" and "adult_male" not in ranges:
            fallback_order = ["adult", "child"]
        elif self._demo_key == "adult_female" and "adult_female" not in ranges:
            fallback_order = ["adult", "child"]

        for key in fallback_order:
            if key in ranges:
                return ranges[key]
        # Return first available
        return next(iter(ranges.values()), None)

    def _generate_summary(self, report: DetectionReport) -> str:
        lines = [f"📊 Analysis of {report.total_tests} lab tests:"]
        lines.append(f"  ✅ Normal: {report.normal_count}")
        if report.critical_count:
            lines.append(f"  🚨 Critical: {report.critical_count}")
        abnormal_non_critical = report.abnormal_count - report.critical_count
        if abnormal_non_critical:
            lines.append(f"  ⚠️  Abnormal: {abnormal_non_critical}")
        return "\n".join(lines)

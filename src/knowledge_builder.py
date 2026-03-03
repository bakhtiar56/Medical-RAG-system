"""Medical knowledge base loader and document generator."""

import json
from pathlib import Path
from typing import Optional

from src.config import KNOWLEDGE_DIR


class MedicalKnowledgeBase:
    """Loads and provides access to the medical knowledge base."""

    def __init__(self):
        self.blood_tests = self._load_json("blood_tests.json").get("blood_tests", {})
        self.urine_tests = self._load_json("urine_tests.json").get("urine_tests", {})
        self.stool_tests = self._load_json("stool_tests.json").get("stool_tests", {})
        self.conditions = self._load_json("conditions_database.json").get("conditions", {})
        self.specialists = self._load_json("specialist_mapping.json").get("specialists", {})
        self.urgency_levels = self._load_json("specialist_mapping.json").get("urgency_levels", {})
        self.critical_values = self._load_json("critical_values.json").get("critical_values", {})
        self.all_tests = {**self.blood_tests, **self.urine_tests, **self.stool_tests}

    def _load_json(self, filename: str) -> dict:
        path = KNOWLEDGE_DIR / filename
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_test_info(self, test_name: str) -> Optional[dict]:
        return self.all_tests.get(test_name)

    def get_condition_info(self, condition_id: str) -> Optional[dict]:
        return self.conditions.get(condition_id)

    def get_specialist_info(self, specialist_id: str) -> Optional[dict]:
        return self.specialists.get(specialist_id)

    def get_critical_value(self, test_name: str) -> Optional[dict]:
        return self.critical_values.get(test_name)

    def generate_documents_for_vectordb(self) -> list[dict]:
        """Generate documents for vector database indexing."""
        docs = []
        for test_name, test_info in self.all_tests.items():
            docs.append({
                "content": self._format_test_document(test_name, test_info),
                "metadata": {"type": "test", "id": test_name},
            })
        for cond_id, cond_info in self.conditions.items():
            docs.append({
                "content": self._format_condition_document(cond_id, cond_info),
                "metadata": {"type": "condition", "id": cond_id},
            })
        for spec_id, spec_info in self.specialists.items():
            docs.append({
                "content": self._format_specialist_document(spec_id, spec_info),
                "metadata": {"type": "specialist", "id": spec_id},
            })
        return docs

    def _format_test_document(self, test_name: str, test_info: dict) -> str:
        lines = [f"Medical Test: {test_name.replace('_', ' ').title()}"]
        if "description" in test_info:
            lines.append(f"Description: {test_info['description']}")
        if "unit" in test_info:
            lines.append(f"Unit: {test_info['unit']}")
        if "normal_ranges" in test_info:
            ranges = []
            for group, r in test_info["normal_ranges"].items():
                if isinstance(r, dict):
                    ranges.append(f"{group}: {r.get('min', '?')}-{r.get('max', '?')}")
            if ranges:
                lines.append(f"Normal ranges: {', '.join(ranges)}")
        if "low_conditions" in test_info and test_info["low_conditions"]:
            lines.append(f"Low value associated with: {', '.join(test_info['low_conditions'])}")
        if "high_conditions" in test_info and test_info["high_conditions"]:
            lines.append(f"High value associated with: {', '.join(test_info['high_conditions'])}")
        return "\n".join(lines)

    def _format_condition_document(self, cond_id: str, cond_info: dict) -> str:
        lines = [f"Medical Condition: {cond_info.get('name', cond_id)}"]
        if "description" in cond_info:
            lines.append(f"Description: {cond_info['description']}")
        if "category" in cond_info:
            lines.append(f"Category: {cond_info['category']}")
        if "severity" in cond_info:
            lines.append(f"Severity: {cond_info['severity']}")
        if "symptoms" in cond_info:
            lines.append(f"Symptoms: {', '.join(cond_info['symptoms'])}")
        if "key_markers" in cond_info:
            lines.append(f"Key lab markers: {', '.join(cond_info['key_markers'])}")
        if "risk_factors" in cond_info:
            lines.append(f"Risk factors: {', '.join(cond_info['risk_factors'])}")
        return "\n".join(lines)

    def _format_specialist_document(self, spec_id: str, spec_info: dict) -> str:
        lines = [f"Medical Specialist: {spec_info.get('title', spec_id)}"]
        if "description" in spec_info:
            lines.append(f"Description: {spec_info['description']}")
        if "conditions" in spec_info and spec_info["conditions"]:
            lines.append(f"Treats conditions: {', '.join(spec_info['conditions'])}")
        return "\n".join(lines)

"""Specialist recommendation module."""

from dataclasses import dataclass, field

from src.knowledge_builder import MedicalKnowledgeBase


@dataclass
class SpecialistRecommendation:
    specialist_id: str
    specialist_title: str
    specialist_description: str
    conditions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    urgency: str = "routine"
    urgency_color: str = "yellow"
    urgency_description: str = ""


class SpecialistRecommender:
    """Recommends medical specialists based on diagnoses."""

    URGENCY_ORDER = {"urgent": 0, "soon": 1, "routine": 2, "monitor": 3}
    URGENCY_EMOJIS = {"urgent": "🔴", "soon": "🟠", "routine": "🟡", "monitor": "🟢"}

    def __init__(self):
        self.kb = MedicalKnowledgeBase()
        self._recommendations: list[SpecialistRecommendation] = []

    def recommend(self, final_diagnoses: list) -> list[SpecialistRecommendation]:
        """Map conditions to specialists and aggregate recommendations."""
        specialist_map: dict[str, dict] = {}

        for candidate in final_diagnoses:
            cond_id = candidate.condition_id
            cond_info = self.kb.get_condition_info(cond_id)
            if cond_info is None:
                continue

            spec_id = cond_info.get("specialist", "general_practitioner")
            spec_info = self.kb.get_specialist_info(spec_id)
            if spec_info is None:
                continue

            urgency = cond_info.get("urgency", "routine")

            if spec_id not in specialist_map:
                urgency_info = self.kb.urgency_levels.get(urgency, {})
                specialist_map[spec_id] = {
                    "title": spec_info.get("title", spec_id),
                    "description": spec_info.get("description", ""),
                    "conditions": [],
                    "confidence_sum": 0.0,
                    "urgency": urgency,
                    "urgency_color": urgency_info.get("color", "yellow"),
                    "urgency_description": urgency_info.get("description", ""),
                }

            specialist_map[spec_id]["conditions"].append(cond_id)
            specialist_map[spec_id]["confidence_sum"] += candidate.confidence

            # Use most urgent level
            current_urgency = specialist_map[spec_id]["urgency"]
            if self.URGENCY_ORDER.get(urgency, 99) < self.URGENCY_ORDER.get(current_urgency, 99):
                urgency_info = self.kb.urgency_levels.get(urgency, {})
                specialist_map[spec_id]["urgency"] = urgency
                specialist_map[spec_id]["urgency_color"] = urgency_info.get("color", "yellow")
                specialist_map[spec_id]["urgency_description"] = urgency_info.get("description", "")

        self._recommendations = []
        for spec_id, data in specialist_map.items():
            avg_conf = data["confidence_sum"] / max(len(data["conditions"]), 1)
            self._recommendations.append(SpecialistRecommendation(
                specialist_id=spec_id,
                specialist_title=data["title"],
                specialist_description=data["description"],
                conditions=data["conditions"],
                confidence=round(avg_conf, 3),
                urgency=data["urgency"],
                urgency_color=data["urgency_color"],
                urgency_description=data["urgency_description"],
            ))

        # Sort by urgency
        self._recommendations.sort(
            key=lambda r: self.URGENCY_ORDER.get(r.urgency, 99)
        )
        return self._recommendations

    def format_recommendations(self) -> str:
        """Format recommendations as readable text."""
        if not self._recommendations:
            return "No specialist referrals needed at this time."

        lines = ["=== Specialist Referral Recommendations ===\n"]
        for rec in self._recommendations:
            emoji = self.URGENCY_EMOJIS.get(rec.urgency, "⬜")
            lines.append(f"{emoji} {rec.specialist_title} ({rec.urgency.upper()})")
            lines.append(f"   {rec.specialist_description}")
            lines.append(f"   Conditions: {', '.join(rec.conditions)}")
            if rec.urgency_description:
                lines.append(f"   Timing: {rec.urgency_description}")
            lines.append(f"   Confidence: {rec.confidence:.0%}\n")

        return "\n".join(lines)

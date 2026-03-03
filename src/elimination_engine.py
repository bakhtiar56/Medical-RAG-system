"""Process-of-elimination diagnostic engine."""

from dataclasses import dataclass, field
from typing import Optional

from src.abnormality_detector import Severity, TestAbnormality
from src.knowledge_builder import MedicalKnowledgeBase


@dataclass
class ConditionCandidate:
    condition_id: str
    condition_name: str
    confidence: float
    matching_markers: list[str] = field(default_factory=list)
    eliminated: bool = False
    elimination_reason: str = ""


@dataclass
class EliminationQuestion:
    question_id: str
    question_text: str
    target_conditions: list[str] = field(default_factory=list)
    asked: bool = False
    answer: Optional[str] = None


@dataclass
class EliminationState:
    candidates: list[ConditionCandidate] = field(default_factory=list)
    questions: list[EliminationQuestion] = field(default_factory=list)
    round_number: int = 0
    completed: bool = False
    patient_answers: dict = field(default_factory=dict)


class EliminationEngine:
    """Diagnostic engine using process-of-elimination."""

    MAX_ROUNDS = 5
    CONFIDENCE_BOOST_YES = 0.15
    CONFIDENCE_PENALTY_NO = 0.20
    ELIMINATION_THRESHOLD = 0.15
    DIAGNOSIS_THRESHOLD = 0.65
    MAX_FINAL_DIAGNOSES = 3

    def __init__(self):
        self.kb = MedicalKnowledgeBase()
        self.state = EliminationState()

    def seed_candidates(self, abnormalities: list[TestAbnormality]) -> EliminationState:
        """Build initial condition candidates from detected abnormalities."""
        condition_scores: dict[str, dict] = {}

        severity_weights = {
            Severity.CRITICAL: 0.3,
            Severity.ABNORMAL: 0.2,
            Severity.BORDERLINE: 0.1,
        }

        for abn in abnormalities:
            sev_weight = severity_weights.get(abn.severity, 0.1)
            for condition_id in abn.possible_conditions:
                if condition_id not in condition_scores:
                    cond_info = self.kb.get_condition_info(condition_id)
                    if cond_info is None:
                        continue
                    condition_scores[condition_id] = {
                        "name": cond_info.get("name", condition_id),
                        "key_markers": cond_info.get("key_markers", []),
                        "matching": set(),
                        "severity_sum": 0.0,
                    }
                condition_scores[condition_id]["matching"].add(abn.test_name)
                condition_scores[condition_id]["severity_sum"] += sev_weight

        candidates = []
        for cond_id, data in condition_scores.items():
            key_markers = data["key_markers"]
            matching = data["matching"]
            marker_ratio = len(matching) / max(len(key_markers), 1)
            severity_weight = min(data["severity_sum"], 1.0)
            confidence = (marker_ratio * 0.6) + (severity_weight * 0.4)
            confidence = round(min(confidence, 1.0), 3)
            candidates.append(ConditionCandidate(
                condition_id=cond_id,
                condition_name=data["name"],
                confidence=confidence,
                matching_markers=list(matching),
            ))

        # Sort by confidence descending
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        self.state.candidates = candidates
        self.state.questions = self._generate_questions()
        return self.state

    def _generate_questions(self) -> list[EliminationQuestion]:
        """Generate follow-up questions from top candidates."""
        questions = []
        seen_texts: set[str] = set()
        question_condition_map: dict[str, list[str]] = {}

        top_candidates = [c for c in self.state.candidates if not c.eliminated][:5]

        for candidate in top_candidates:
            cond_info = self.kb.get_condition_info(candidate.condition_id)
            if cond_info is None:
                continue
            for q_text in cond_info.get("follow_up_questions", []):
                if q_text not in question_condition_map:
                    question_condition_map[q_text] = []
                question_condition_map[q_text].append(candidate.condition_id)

        # Prioritize questions that affect multiple conditions
        sorted_questions = sorted(
            question_condition_map.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

        for q_text, conditions in sorted_questions:
            if q_text in seen_texts:
                continue
            seen_texts.add(q_text)
            q_id = f"q_{len(questions)}"
            questions.append(EliminationQuestion(
                question_id=q_id,
                question_text=q_text,
                target_conditions=conditions,
            ))

        return questions

    def get_next_questions(self, n: int = 3) -> list[EliminationQuestion]:
        """Get next unasked questions."""
        return [q for q in self.state.questions if not q.asked][:n]

    def process_answer(self, question_id: str, answer: str) -> None:
        """Process a single answer. answer is 'Yes', 'No', or 'Not sure'."""
        question = next((q for q in self.state.questions if q.question_id == question_id), None)
        if question is None:
            return
        question.asked = True
        question.answer = answer
        self.state.patient_answers[question_id] = answer

        if answer.lower() == "yes":
            for cond_id in question.target_conditions:
                self._adjust_confidence(cond_id, self.CONFIDENCE_BOOST_YES)
        elif answer.lower() == "no":
            for cond_id in question.target_conditions:
                self._adjust_confidence(cond_id, -self.CONFIDENCE_PENALTY_NO)
                # Eliminate if below threshold
                candidate = self._get_candidate(cond_id)
                if candidate and candidate.confidence < self.ELIMINATION_THRESHOLD:
                    candidate.eliminated = True
                    candidate.elimination_reason = f"Confidence dropped below {self.ELIMINATION_THRESHOLD}"

        self.state.round_number += 1
        self._check_completion()

    def process_batch_answers(self, answers: dict) -> None:
        """Process multiple answers at once. answers is {question_id: answer}."""
        for q_id, answer in answers.items():
            self.process_answer(q_id, answer)

    def _adjust_confidence(self, condition_id: str, delta: float) -> None:
        candidate = self._get_candidate(condition_id)
        if candidate:
            candidate.confidence = round(max(0.0, min(1.0, candidate.confidence + delta)), 3)

    def _get_candidate(self, condition_id: str) -> Optional[ConditionCandidate]:
        return next((c for c in self.state.candidates if c.condition_id == condition_id), None)

    def _check_completion(self) -> None:
        """Check if elimination process should end."""
        active = [c for c in self.state.candidates if not c.eliminated]
        unanswered = [q for q in self.state.questions if not q.asked]

        if self.state.round_number >= self.MAX_ROUNDS:
            self.state.completed = True
        elif len(active) <= self.MAX_FINAL_DIAGNOSES:
            self.state.completed = True
        elif active and active[0].confidence >= self.DIAGNOSIS_THRESHOLD:
            self.state.completed = True
        elif not unanswered:
            self.state.completed = True

    def force_conclude(self) -> None:
        """Force completion of elimination process."""
        self.state.completed = True

    def get_elimination_summary(self) -> str:
        """Generate human-readable summary of elimination process."""
        lines = ["=== Diagnostic Elimination Summary ==="]
        active = [c for c in self.state.candidates if not c.eliminated]
        eliminated = [c for c in self.state.candidates if c.eliminated]

        lines.append(f"\nRounds completed: {self.state.round_number}")
        lines.append(f"Active candidates: {len(active)}")
        lines.append(f"Eliminated conditions: {len(eliminated)}")

        if active:
            lines.append("\n📋 Top Diagnoses:")
            for i, c in enumerate(active[:self.MAX_FINAL_DIAGNOSES], 1):
                lines.append(f"  {i}. {c.condition_name}: {c.confidence:.0%} confidence")

        if eliminated:
            lines.append("\n❌ Eliminated:")
            for c in eliminated:
                lines.append(f"  - {c.condition_name}: {c.elimination_reason}")

        return "\n".join(lines)

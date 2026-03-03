"""Main RAG pipeline orchestrating the diagnostic workflow."""

from dataclasses import dataclass, field
from typing import Optional

from src.abnormality_detector import AbnormalityDetector, DetectionReport
from src.elimination_engine import EliminationEngine, EliminationState
from src.knowledge_builder import MedicalKnowledgeBase
from src.report_parser import MedicalReportParser
from src.specialist_recommender import SpecialistRecommender


@dataclass
class PatientInfo:
    age: int = 35
    sex: str = "adult"
    existing_conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)


@dataclass
class DiagnosticSession:
    session_id: str = ""
    patient_info: Optional[PatientInfo] = None
    parsed_results: list[dict] = field(default_factory=list)
    detection_report: Optional[DetectionReport] = None
    elimination_state: Optional[EliminationState] = None
    diagnosis: str = ""
    specialist_recommendations: list = field(default_factory=list)
    stage: str = "init"


class MedicalRAGPipeline:
    """End-to-end medical diagnostic pipeline."""

    MAX_RECOMMENDATIONS = 4  # Maximum number of top candidates passed to specialist recommender

    def __init__(self):
        self.kb = MedicalKnowledgeBase()
        self.parser = MedicalReportParser()
        self.recommender = SpecialistRecommender()
        self._reasoner = None  # Lazy-loaded
        self._vector_store = None  # Lazy-loaded
        self.session = DiagnosticSession()

    def _get_reasoner(self):
        if self._reasoner is None:
            from src.diagnostic_reasoner import DiagnosticReasoner
            self._reasoner = DiagnosticReasoner(vector_store=self._vector_store)
        return self._reasoner

    def start_session(self, patient_info: Optional[PatientInfo] = None) -> DiagnosticSession:
        """Initialize a new diagnostic session."""
        import uuid
        self.session = DiagnosticSession(
            session_id=str(uuid.uuid4())[:8],
            patient_info=patient_info,
            stage="input",
        )
        return self.session

    def input_pdf(self, pdf_path: str) -> list[dict]:
        """Parse a PDF report."""
        self.session.parsed_results = self.parser.parse_pdf(pdf_path)
        self.session.stage = "parsed"
        return self.session.parsed_results

    def input_text(self, text: str) -> list[dict]:
        """Parse plain text report."""
        self.session.parsed_results = self.parser.parse_text(text)
        self.session.stage = "parsed"
        return self.session.parsed_results

    def input_form(self, test_data: dict) -> list[dict]:
        """Parse structured form input."""
        self.session.parsed_results = self.parser.parse_structured_input(test_data)
        self.session.stage = "parsed"
        return self.session.parsed_results

    def detect_abnormalities(self) -> DetectionReport:
        """Detect abnormalities in parsed results."""
        if not self.session.parsed_results:
            raise ValueError("No parsed results available. Run input first.")
        patient = self.session.patient_info or PatientInfo()
        detector = AbnormalityDetector(
            patient_sex=patient.sex,
            patient_age=patient.age,
        )
        self.session.detection_report = detector.analyze(self.session.parsed_results)
        self.session.stage = "detected"
        return self.session.detection_report

    def start_elimination(self) -> EliminationState:
        """Begin the diagnostic elimination process."""
        if self.session.detection_report is None:
            raise ValueError("No detection report. Run detect_abnormalities first.")
        engine = EliminationEngine()
        engine.seed_candidates(self.session.detection_report.abnormalities)
        self.session.elimination_state = engine.state
        self._engine = engine
        self.session.stage = "elimination"
        return self.session.elimination_state

    def get_questions(self, n: int = 3) -> list:
        """Get next diagnostic questions."""
        if not hasattr(self, "_engine"):
            return []
        return self._engine.get_next_questions(n)

    def answer_question(self, question_id: str, answer: str) -> EliminationState:
        """Answer a diagnostic question."""
        if hasattr(self, "_engine"):
            self._engine.process_answer(question_id, answer)
        return self.session.elimination_state

    def answer_questions_batch(self, answers: dict) -> EliminationState:
        """Answer multiple questions at once."""
        if hasattr(self, "_engine"):
            self._engine.process_batch_answers(answers)
        return self.session.elimination_state

    def skip_questions(self) -> None:
        """Skip remaining questions and force conclusion."""
        if hasattr(self, "_engine"):
            self._engine.force_conclude()
        if self.session.elimination_state:
            self.session.elimination_state.completed = True

    def generate_diagnosis(self) -> str:
        """Generate LLM-powered diagnosis."""
        if self.session.detection_report is None:
            raise ValueError("No detection report available.")

        patient_dict = {}
        if self.session.patient_info:
            p = self.session.patient_info
            patient_dict = {"age": p.age, "sex": p.sex}

        try:
            diagnosis = self._get_reasoner().generate_diagnosis(
                self.session.detection_report,
                self.session.elimination_state or EliminationState(),
                patient_dict,
            )
        except Exception:
            diagnosis = self._rule_based_diagnosis()

        self.session.diagnosis = diagnosis
        self.session.stage = "diagnosed"
        return diagnosis

    def recommend_specialists(self) -> list:
        """Generate specialist recommendations."""
        if self.session.elimination_state is None:
            return []
        active = [c for c in self.session.elimination_state.candidates if not c.eliminated]
        recs = self.recommender.recommend(active[:self.MAX_RECOMMENDATIONS])
        self.session.specialist_recommendations = recs
        self.session.stage = "complete"
        return recs

    def ask_followup(self, question: str) -> str:
        """Ask a follow-up question about the diagnosis."""
        if not self.session.diagnosis:
            return "No diagnosis has been generated yet."
        return self._get_reasoner().answer_followup(question, self.session.diagnosis)

    def _rule_based_diagnosis(self) -> str:
        """Fallback rule-based diagnosis when API is unavailable."""
        report = self.session.detection_report
        lines = ["## Medical Report Analysis\n"]
        lines.append(f"**Total tests analyzed:** {report.total_tests}")
        lines.append(f"**Abnormal findings:** {report.abnormal_count}")
        lines.append(f"**Critical values:** {report.critical_count}\n")

        if report.abnormalities:
            lines.append("### Abnormal Findings:")
            for abn in report.abnormalities:
                lines.append(f"- **{abn.test_name}**: {abn.value} [{abn.severity.value.upper()}]")
                if abn.possible_conditions:
                    lines.append(f"  Possible conditions: {', '.join(abn.possible_conditions)}")

        lines.append("\n> ⚠️ **Disclaimer**: This is a preliminary assessment only. Please consult a qualified healthcare professional for proper medical advice.")
        return "\n".join(lines)

    def run_full_pipeline(self, input_data: dict, patient_info: Optional[PatientInfo] = None) -> DiagnosticSession:
        """Run the complete pipeline automatically."""
        self.start_session(patient_info)
        self.input_form(input_data)
        self.detect_abnormalities()
        self.start_elimination()
        self.skip_questions()
        try:
            self.generate_diagnosis()
        except Exception:
            self.session.diagnosis = self._rule_based_diagnosis()
        self.recommend_specialists()
        return self.session

    def get_session_summary(self) -> str:
        """Get complete session summary."""
        lines = ["=" * 60, "MEDICAL DIAGNOSTIC SESSION SUMMARY", "=" * 60]
        if self.session.detection_report:
            lines.append(self.session.detection_report.summary)
        if self.session.elimination_state and hasattr(self, "_engine"):
            lines.append(self._engine.get_elimination_summary())
        if self.session.diagnosis:
            lines.append("\n### Diagnosis\n")
            lines.append(self.session.diagnosis)
        if self.session.specialist_recommendations:
            lines.append(self.recommender.format_recommendations())
        lines.append("\n> ⚠️ Disclaimer: For educational purposes only. Consult a healthcare professional.")
        return "\n".join(lines)

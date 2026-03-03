"""LLM-powered diagnostic reasoning module."""

from typing import Optional

from src.config import LLM_MODEL, OPENAI_API_KEY
from src.abnormality_detector import DetectionReport
from src.elimination_engine import EliminationState


SYSTEM_PROMPT = """You are an expert medical diagnostic assistant with deep knowledge of clinical pathology and laboratory medicine.

You analyze laboratory test results and provide comprehensive diagnostic assessments based on the data provided.

IMPORTANT DISCLAIMERS:
- This analysis is for educational purposes only and does not constitute medical advice
- Always recommend consulting qualified healthcare professionals
- Do not make definitive diagnoses - provide differential diagnoses and likelihood assessments
- Emphasize the importance of clinical correlation and follow-up testing

Your analysis should be thorough, evidence-based, and presented in a clear, structured format."""

USER_PROMPT_TEMPLATE = """Please analyze the following medical laboratory findings and provide a comprehensive diagnostic assessment.

## Patient Information
{patient_info}

## Detected Abnormalities
{abnormalities}

## Diagnostic Elimination Results
{elimination_results}

## Patient's Symptom Responses
{patient_responses}

## Relevant Medical Context
{context}

Please provide:
1. **Executive Summary**: Brief overview of key findings
2. **Detailed Analysis**: Analysis of each abnormal finding
3. **Diagnostic Reasoning**: Most likely diagnoses with confidence levels and reasoning
4. **Recommended Consultations**: Which specialists to see and when
5. **Additional Tests**: Recommended follow-up tests
6. **Patient-Friendly Explanation**: Simple language explanation of findings

Remember to include appropriate medical disclaimers."""


class DiagnosticReasoner:
    """Uses LLM to generate comprehensive diagnostic assessments."""

    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self._llm = None
        self._chain = None

    def _get_llm(self):
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=0.1,
                openai_api_key=OPENAI_API_KEY,
            )
        return self._llm

    def generate_diagnosis(
        self,
        detection_report: DetectionReport,
        elimination_state: EliminationState,
        patient_info: Optional[dict] = None,
    ) -> str:
        """Generate a comprehensive diagnosis using LLM."""
        context = ""
        if self.vector_store:
            try:
                query = self._build_retrieval_query(detection_report, elimination_state)
                docs = self.vector_store.similarity_search(query, k=5)
                context = self._format_context(docs)
            except Exception:
                context = "Medical knowledge base context unavailable."

        prompt = USER_PROMPT_TEMPLATE.format(
            patient_info=self._format_patient_info(patient_info),
            abnormalities=self._format_abnormalities(detection_report),
            elimination_results=self._format_elimination_results(elimination_state),
            patient_responses=self._format_patient_responses(elimination_state),
            context=context or "No additional context available.",
        )

        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self._get_llm().invoke(messages)
        return response.content

    def answer_followup(self, question: str, diagnosis_context: str) -> str:
        """Answer a patient follow-up question."""
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Previous diagnosis context:\n{diagnosis_context}\n\nPatient question: {question}"),
        ]
        response = self._get_llm().invoke(messages)
        return response.content

    def _build_retrieval_query(self, detection_report: DetectionReport, elimination_state: EliminationState) -> str:
        parts = []
        for abn in detection_report.abnormalities[:3]:
            parts.append(abn.test_name.replace("_", " "))
        active = [c for c in elimination_state.candidates if not c.eliminated]
        for c in active[:2]:
            parts.append(c.condition_name)
        return " ".join(parts)

    def _format_context(self, docs: list) -> str:
        return "\n\n".join(d.page_content for d in docs)

    def _format_patient_info(self, patient_info: Optional[dict]) -> str:
        if not patient_info:
            return "Not provided"
        return "\n".join(f"- {k}: {v}" for k, v in patient_info.items())

    def _format_abnormalities(self, report: DetectionReport) -> str:
        if not report.abnormalities:
            return "No abnormalities detected"
        lines = []
        for abn in report.abnormalities:
            direction = f" ({abn.direction})" if abn.direction else ""
            lines.append(f"- {abn.test_name}: {abn.value} [{abn.severity.value.upper()}{direction}] - {abn.message}")
        return "\n".join(lines)

    def _format_elimination_results(self, state: EliminationState) -> str:
        active = [c for c in state.candidates if not c.eliminated]
        if not active:
            return "No diagnostic candidates identified"
        lines = []
        for c in active[:5]:
            lines.append(f"- {c.condition_name}: {c.confidence:.0%} confidence")
        return "\n".join(lines)

    def _format_patient_responses(self, state: EliminationState) -> str:
        answered = [(q.question_text, q.answer) for q in state.questions if q.asked]
        if not answered:
            return "No patient responses recorded"
        return "\n".join(f"- Q: {q}\n  A: {a}" for q, a in answered)

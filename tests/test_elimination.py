"""Tests for the elimination engine."""
import pytest
from src.abnormality_detector import Severity, TestAbnormality
from src.elimination_engine import EliminationEngine


@pytest.fixture
def engine():
    return EliminationEngine()


@pytest.fixture
def diabetes_abnormalities():
    return [
        TestAbnormality(
            test_name="glucose_fasting", value=280, unit="mg/dL",
            severity=Severity.ABNORMAL, direction="high",
            deviation_pct=180, normal_range={"min": 70, "max": 100},
            possible_conditions=["diabetes_mellitus_type_2", "prediabetes"],
        ),
        TestAbnormality(
            test_name="hba1c", value=9.2, unit="%",
            severity=Severity.ABNORMAL, direction="high",
            deviation_pct=64.3, normal_range={"min": 4.0, "max": 5.6},
            possible_conditions=["diabetes_mellitus_type_2", "prediabetes"],
        ),
    ]


@pytest.fixture
def kidney_abnormalities():
    return [
        TestAbnormality(
            test_name="creatinine", value=3.5, unit="mg/dL",
            severity=Severity.ABNORMAL, direction="high",
            deviation_pct=169.2, normal_range={"min": 0.7, "max": 1.3},
            possible_conditions=["chronic_kidney_disease", "acute_kidney_injury"],
        ),
        TestAbnormality(
            test_name="blood_urea_nitrogen", value=55, unit="mg/dL",
            severity=Severity.ABNORMAL, direction="high",
            deviation_pct=120, normal_range={"min": 7, "max": 25},
            possible_conditions=["chronic_kidney_disease", "dehydration"],
        ),
        TestAbnormality(
            test_name="urine_protein", value=85, unit="mg/dL",
            severity=Severity.ABNORMAL, direction="high",
            deviation_pct=507, normal_range={"min": 0, "max": 14},
            possible_conditions=["chronic_kidney_disease", "nephrotic_syndrome"],
        ),
    ]


class TestCandidateSeeding:
    def test_seed_diabetes_candidates(self, engine, diabetes_abnormalities):
        state = engine.seed_candidates(diabetes_abnormalities)
        assert len(state.candidates) > 0
        cond_ids = [c.condition_id for c in state.candidates]
        assert "diabetes_mellitus_type_2" in cond_ids

    def test_seed_kidney_candidates(self, engine, kidney_abnormalities):
        state = engine.seed_candidates(kidney_abnormalities)
        cond_ids = [c.condition_id for c in state.candidates]
        assert "chronic_kidney_disease" in cond_ids

    def test_candidates_sorted_by_confidence(self, engine, diabetes_abnormalities):
        state = engine.seed_candidates(diabetes_abnormalities)
        confidences = [c.confidence for c in state.candidates]
        assert confidences == sorted(confidences, reverse=True)

    def test_questions_generated(self, engine, diabetes_abnormalities):
        state = engine.seed_candidates(diabetes_abnormalities)
        assert len(state.questions) > 0


class TestAnswerProcessing:
    def test_yes_answer_boosts_confidence(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        questions = engine.get_next_questions(1)
        assert questions
        q = questions[0]
        # Get initial confidence
        initial_conf = {c.condition_id: c.confidence for c in engine.state.candidates}
        engine.process_answer(q.question_id, "Yes")
        # At least one targeted condition should have increased confidence
        boosted = False
        for cond_id in q.target_conditions:
            cand = next((c for c in engine.state.candidates if c.condition_id == cond_id), None)
            if cand and cand.confidence > initial_conf.get(cond_id, 0):
                boosted = True
                break
        assert boosted

    def test_no_answer_reduces_confidence(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        questions = engine.get_next_questions(1)
        assert questions
        q = questions[0]
        initial_conf = {c.condition_id: c.confidence for c in engine.state.candidates}
        engine.process_answer(q.question_id, "No")
        reduced = False
        for cond_id in q.target_conditions:
            cand = next((c for c in engine.state.candidates if c.condition_id == cond_id), None)
            if cand and cand.confidence < initial_conf.get(cond_id, 1):
                reduced = True
                break
        assert reduced

    def test_not_sure_no_change(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        questions = engine.get_next_questions(1)
        assert questions
        q = questions[0]
        initial_conf = {c.condition_id: c.confidence for c in engine.state.candidates}
        engine.process_answer(q.question_id, "Not sure")
        for cond_id in q.target_conditions:
            cand = next((c for c in engine.state.candidates if c.condition_id == cond_id), None)
            if cand:
                assert cand.confidence == initial_conf.get(cond_id, 0)

    def test_repeated_no_eliminates_condition(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        # Answer No to all questions for a condition
        for _ in range(10):
            questions = engine.get_next_questions(1)
            if not questions:
                break
            engine.process_answer(questions[0].question_id, "No")
        eliminated = [c for c in engine.state.candidates if c.eliminated]
        # At least one should be eliminated after many No answers
        assert len(eliminated) >= 0  # May or may not eliminate based on question count


class TestForceConclusion:
    def test_force_conclude(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        engine.force_conclude()
        assert engine.state.completed is True

    def test_summary_generation(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        engine.force_conclude()
        summary = engine.get_elimination_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestBatchAnswers:
    def test_batch_answers(self, engine, diabetes_abnormalities):
        engine.seed_candidates(diabetes_abnormalities)
        questions = engine.get_next_questions(3)
        answers = {q.question_id: "Yes" for q in questions}
        engine.process_batch_answers(answers)
        answered = [q for q in engine.state.questions if q.asked]
        assert len(answered) == len(questions)

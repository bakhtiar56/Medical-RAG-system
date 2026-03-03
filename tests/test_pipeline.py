"""Tests for the RAG pipeline."""
import pytest
from src.rag_pipeline import MedicalRAGPipeline, PatientInfo


@pytest.fixture
def pipeline():
    return MedicalRAGPipeline()


class TestSessionManagement:
    def test_start_session(self, pipeline):
        session = pipeline.start_session()
        assert session.session_id != ""
        assert session.stage == "input"

    def test_start_session_with_patient_info(self, pipeline):
        patient = PatientInfo(age=52, sex="male")
        session = pipeline.start_session(patient)
        assert session.patient_info is not None
        assert session.patient_info.age == 52


class TestInputParsing:
    def test_form_input(self, pipeline):
        pipeline.start_session()
        data = {
            "hemoglobin": 10.5,
            "glucose_fasting": 280,
            "white_blood_cells": 12000,
            "creatinine": 2.1,
            "tsh": 8.5,
            "alt": 120,
            "urine_blood": "positive",
        }
        results = pipeline.input_form(data)
        assert len(results) == 7

    def test_text_input(self, pipeline):
        pipeline.start_session()
        text = "Hemoglobin: 10.5 g/dL\nGlucose fasting: 280 mg/dL"
        results = pipeline.input_text(text)
        assert len(results) >= 1


class TestDetectionStage:
    def test_detect_abnormalities(self, pipeline):
        pipeline.start_session(PatientInfo(age=45, sex="male"))
        pipeline.input_form({
            "hemoglobin": 6.5,
            "glucose_fasting": 280,
        })
        report = pipeline.detect_abnormalities()
        assert report.abnormal_count > 0

    def test_detect_requires_parsed_results(self, pipeline):
        pipeline.start_session()
        with pytest.raises(ValueError):
            pipeline.detect_abnormalities()


class TestEliminationStage:
    def test_start_elimination(self, pipeline):
        pipeline.start_session(PatientInfo(age=45, sex="male"))
        pipeline.input_form({"glucose_fasting": 280, "hba1c": 9.5})
        pipeline.detect_abnormalities()
        state = pipeline.start_elimination()
        assert state is not None
        assert len(state.candidates) > 0

    def test_skip_questions(self, pipeline):
        pipeline.start_session()
        pipeline.input_form({"glucose_fasting": 280})
        pipeline.detect_abnormalities()
        pipeline.start_elimination()
        pipeline.skip_questions()
        assert pipeline.session.elimination_state.completed is True

    def test_elimination_requires_detection(self, pipeline):
        pipeline.start_session()
        with pytest.raises(ValueError):
            pipeline.start_elimination()


class TestGetQuestions:
    def test_get_questions(self, pipeline):
        pipeline.start_session()
        pipeline.input_form({"glucose_fasting": 280, "hba1c": 9.5})
        pipeline.detect_abnormalities()
        pipeline.start_elimination()
        questions = pipeline.get_questions(3)
        assert isinstance(questions, list)

    def test_answer_question(self, pipeline):
        pipeline.start_session()
        pipeline.input_form({"glucose_fasting": 280})
        pipeline.detect_abnormalities()
        pipeline.start_elimination()
        questions = pipeline.get_questions(1)
        if questions:
            state = pipeline.answer_question(questions[0].question_id, "Yes")
            assert state is not None

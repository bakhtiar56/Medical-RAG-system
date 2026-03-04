"""Streamlit web application for Medical RAG System."""

import streamlit as st

from src.rag_pipeline import MedicalRAGPipeline, PatientInfo
from src.report_parser import MedicalReportParser

st.set_page_config(
    page_title="MedDiag AI — Medical Report Analyzer",
    page_icon="🏥",
    layout="wide",
)

CUSTOM_CSS = """
<style>
.critical-alert {
    background-color: #ffebee;
    border-left: 4px solid #f44336;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 4px;
}
.abnormal-alert {
    background-color: #fff8e1;
    border-left: 4px solid #ff9800;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 4px;
}
.normal-result {
    background-color: #e8f5e9;
    border-left: 4px solid #4caf50;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 4px;
}
.specialist-card {
    background-color: #f3f4f6;
    border: 1px solid #d1d5db;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
}
.question-card {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
}
.disclaimer {
    background-color: #fef9c3;
    border: 1px solid #fde047;
    padding: 10px;
    border-radius: 6px;
    font-size: 0.85rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

STAGES = [
    ("📋", "Input Reports"),
    ("👤", "Demographics"),
    ("🔍", "Detection"),
    ("❓", "Q&A"),
    ("🧠", "Diagnosis"),
    ("📊", "Results"),
]

STAGE_ORDER = ["input", "demographics", "detection", "questions", "diagnosis", "results"]


def init_state():
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = MedicalRAGPipeline()
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = "input"
    if "test_inputs" not in st.session_state:
        st.session_state.test_inputs = {}
    if "patient_info" not in st.session_state:
        st.session_state.patient_info = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}


def render_sidebar():
    with st.sidebar:
        st.title("🏥 MedDiag AI")
        st.markdown("---")
        st.subheader("Progress")
        current_idx = STAGE_ORDER.index(st.session_state.current_stage)
        for i, (emoji, name) in enumerate(STAGES):
            if i < current_idx:
                st.markdown(f"✅ {emoji} {name}")
            elif i == current_idx:
                st.markdown(f"▶️ **{emoji} {name}**")
            else:
                st.markdown(f"⬜ {emoji} {name}")

        st.markdown("---")
        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.markdown(
            '<div class="disclaimer">⚠️ <b>Disclaimer</b>: This tool is for '
            'educational purposes only and does not provide medical advice. '
            'Always consult a qualified healthcare professional.</div>',
            unsafe_allow_html=True,
        )


def input_stage():
    st.header("📋 Upload Medical Reports")
    st.markdown("Provide your laboratory test results in any of the following formats.")

    method = st.radio(
        "Input method:",
        ["Manual Entry", "Upload PDF", "Paste Text"],
        horizontal=True,
    )

    if method == "Manual Entry":
        tab_blood, tab_urine, tab_stool = st.tabs(["🩸 Blood Tests", "🧪 Urine Tests", "💩 Stool Tests"])

        with tab_blood:
            st.subheader("Complete Blood Count & Panels")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.test_inputs["hemoglobin"] = st.number_input(
                    "Hemoglobin (g/dL)", min_value=0.0, max_value=25.0, value=0.0, step=0.1,
                    key="inp_hgb"
                ) or None
                st.session_state.test_inputs["white_blood_cells"] = st.number_input(
                    "WBC (cells/μL)", min_value=0.0, max_value=100000.0, value=0.0, step=100.0,
                    key="inp_wbc"
                ) or None
                st.session_state.test_inputs["platelets"] = st.number_input(
                    "Platelets (cells/μL)", min_value=0.0, max_value=2000000.0, value=0.0, step=1000.0,
                    key="inp_plt"
                ) or None
                st.session_state.test_inputs["red_blood_cells"] = st.number_input(
                    "RBC (million cells/μL)", min_value=0.0, max_value=10.0, value=0.0, step=0.1,
                    key="inp_rbc"
                ) or None
                st.session_state.test_inputs["mean_corpuscular_volume"] = st.number_input(
                    "MCV (fL)", min_value=0.0, max_value=150.0, value=0.0, step=0.1,
                    key="inp_mcv"
                ) or None
                st.session_state.test_inputs["glucose_fasting"] = st.number_input(
                    "Fasting Glucose (mg/dL)", min_value=0.0, max_value=600.0, value=0.0, step=0.1,
                    key="inp_glu"
                ) or None
                st.session_state.test_inputs["creatinine"] = st.number_input(
                    "Creatinine (mg/dL)", min_value=0.0, max_value=20.0, value=0.0, step=0.01,
                    key="inp_cr"
                ) or None
                st.session_state.test_inputs["blood_urea_nitrogen"] = st.number_input(
                    "BUN (mg/dL)", min_value=0.0, max_value=150.0, value=0.0, step=0.1,
                    key="inp_bun"
                ) or None
            with col2:
                st.session_state.test_inputs["alt"] = st.number_input(
                    "ALT/SGPT (U/L)", min_value=0.0, max_value=5000.0, value=0.0, step=0.1,
                    key="inp_alt"
                ) or None
                st.session_state.test_inputs["ast"] = st.number_input(
                    "AST/SGOT (U/L)", min_value=0.0, max_value=5000.0, value=0.0, step=0.1,
                    key="inp_ast"
                ) or None
                st.session_state.test_inputs["hba1c"] = st.number_input(
                    "HbA1c (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.1,
                    key="inp_hba1c"
                ) or None
                st.session_state.test_inputs["total_cholesterol"] = st.number_input(
                    "Total Cholesterol (mg/dL)", min_value=0.0, max_value=600.0, value=0.0, step=0.1,
                    key="inp_chol"
                ) or None
                st.session_state.test_inputs["ldl_cholesterol"] = st.number_input(
                    "LDL Cholesterol (mg/dL)", min_value=0.0, max_value=400.0, value=0.0, step=0.1,
                    key="inp_ldl"
                ) or None
                st.session_state.test_inputs["triglycerides"] = st.number_input(
                    "Triglycerides (mg/dL)", min_value=0.0, max_value=2000.0, value=0.0, step=0.1,
                    key="inp_tg"
                ) or None
                st.session_state.test_inputs["tsh"] = st.number_input(
                    "TSH (mIU/L)", min_value=0.0, max_value=50.0, value=0.0, step=0.01,
                    key="inp_tsh"
                ) or None
                st.session_state.test_inputs["free_t4"] = st.number_input(
                    "Free T4 (ng/dL)", min_value=0.0, max_value=10.0, value=0.0, step=0.01,
                    key="inp_ft4"
                ) or None

        with tab_urine:
            st.subheader("Urinalysis Panel")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.test_inputs["urine_protein"] = st.number_input(
                    "Urine Protein (mg/dL)", min_value=0.0, max_value=2000.0, value=0.0, step=0.1,
                    key="inp_uprot"
                ) or None
                urine_ph = st.number_input(
                    "Urine pH", min_value=0.0, max_value=14.0, value=0.0, step=0.1,
                    key="inp_uph"
                )
                st.session_state.test_inputs["urine_ph"] = urine_ph if urine_ph > 0 else None
                urine_sg = st.number_input(
                    "Urine Specific Gravity", min_value=0.0, max_value=1.04, value=0.0, step=0.001,
                    format="%.3f", key="inp_usg"
                )
                st.session_state.test_inputs["urine_specific_gravity"] = urine_sg if urine_sg > 0 else None
            with col2:
                st.session_state.test_inputs["urine_glucose"] = st.selectbox(
                    "Urine Glucose", ["", "negative", "positive", "trace"], key="inp_uglu"
                ) or None
                st.session_state.test_inputs["urine_blood"] = st.selectbox(
                    "Urine Blood", ["", "negative", "positive", "trace"], key="inp_ublood"
                ) or None
                st.session_state.test_inputs["urine_ketones"] = st.selectbox(
                    "Urine Ketones", ["", "negative", "positive", "trace"], key="inp_uket"
                ) or None
                st.session_state.test_inputs["leukocyte_esterase"] = st.selectbox(
                    "Leukocyte Esterase", ["", "negative", "positive", "trace"], key="inp_le"
                ) or None
                st.session_state.test_inputs["urine_nitrites"] = st.selectbox(
                    "Urine Nitrites", ["", "negative", "positive"], key="inp_unit"
                ) or None

        with tab_stool:
            st.subheader("Stool Analysis Panel")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.test_inputs["fecal_occult_blood"] = st.selectbox(
                    "Fecal Occult Blood", ["", "negative", "positive"], key="inp_fobt"
                ) or None
                stool_ph = st.number_input(
                    "Stool pH", min_value=0.0, max_value=14.0, value=0.0, step=0.1,
                    key="inp_sph"
                )
                st.session_state.test_inputs["stool_ph"] = stool_ph if stool_ph > 0 else None
                st.session_state.test_inputs["fecal_fat"] = st.number_input(
                    "Fecal Fat (g/24h)", min_value=0.0, max_value=100.0, value=0.0, step=0.1,
                    key="inp_ffat"
                ) or None
                st.session_state.test_inputs["fecal_calprotectin"] = st.number_input(
                    "Fecal Calprotectin (μg/g)", min_value=0.0, max_value=5000.0, value=0.0, step=0.1,
                    key="inp_fcal"
                ) or None
            with col2:
                st.session_state.test_inputs["stool_white_blood_cells"] = st.selectbox(
                    "Stool WBC", ["", "negative", "positive"], key="inp_swbc"
                ) or None
                st.session_state.test_inputs["stool_culture"] = st.selectbox(
                    "Stool Culture", ["", "no_pathogens", "positive"], key="inp_sc"
                ) or None
                st.session_state.test_inputs["ova_and_parasites"] = st.selectbox(
                    "Ova & Parasites", ["", "negative", "positive"], key="inp_op"
                ) or None

    elif method == "Upload PDF":
        uploaded = st.file_uploader("Upload PDF Report", type=["pdf"])
        if uploaded:
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                parser = MedicalReportParser()
                results = parser.parse_pdf(tmp_path)
                st.session_state.test_inputs = {r["test_name"]: r["value"] for r in results}
                st.success(f"✅ Parsed {len(results)} tests from PDF")
            except Exception as e:
                st.error(f"Error parsing PDF: {e}")
            finally:
                os.unlink(tmp_path)

    elif method == "Paste Text":
        text = st.text_area("Paste your lab report here:", height=200)
        if text:
            parser = MedicalReportParser()
            results = parser.parse_text(text)
            st.session_state.test_inputs = {r["test_name"]: r["value"] for r in results}
            if results:
                st.success(f"✅ Detected {len(results)} tests")

    # Clean None values
    st.session_state.test_inputs = {k: v for k, v in st.session_state.test_inputs.items() if v is not None and v != ""}

    if st.button("➡️ Continue", type="primary", use_container_width=True):
        if not st.session_state.test_inputs:
            st.error("Please enter at least one test result.")
        else:
            st.session_state.current_stage = "demographics"
            st.rerun()


def demographics_stage():
    st.header("👤 Patient Demographics")
    st.markdown("Provide patient information to improve diagnostic accuracy.")

    col1, col2 = st.columns(2)
    with col1:
        age = st.slider("Age", min_value=1, max_value=100, value=35)
        sex = st.radio("Biological Sex", ["Male", "Female"], horizontal=True)
    with col2:
        conditions = st.multiselect(
            "Existing Conditions (if any)",
            ["Diabetes", "Hypertension", "Heart Disease", "Kidney Disease", "Thyroid Disorder", "Anemia"],
        )
        medications = st.text_input("Current Medications (comma-separated)")

    if st.button("➡️ Analyze Results", type="primary", use_container_width=True):
        patient = PatientInfo(
            age=age,
            sex=sex.lower(),
            existing_conditions=conditions,
            medications=[m.strip() for m in medications.split(",") if m.strip()],
        )
        st.session_state.patient_info = patient
        pipeline: MedicalRAGPipeline = st.session_state.pipeline
        pipeline.start_session(patient)
        pipeline.input_form(st.session_state.test_inputs)
        st.session_state.current_stage = "detection"
        st.rerun()


def detection_stage():
    st.header("🔍 Abnormality Detection Results")
    pipeline: MedicalRAGPipeline = st.session_state.pipeline

    with st.spinner("Analyzing lab results..."):
        try:
            report = pipeline.detect_abnormalities()
        except Exception as e:
            st.error(f"Error during detection: {e}")
            return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tests", report.total_tests)
    col2.metric("Normal", report.normal_count, delta_color="normal")
    col3.metric("Abnormal", report.abnormal_count, delta_color="inverse" if report.abnormal_count > 0 else "normal")
    col4.metric("⚠️ Critical", report.critical_count, delta_color="inverse" if report.critical_count > 0 else "normal")

    st.markdown("---")

    from src.abnormality_detector import Severity
    critical = [a for a in report.abnormalities if a.severity == Severity.CRITICAL]
    abnormal = [a for a in report.abnormalities if a.severity == Severity.ABNORMAL]
    borderline = [a for a in report.abnormalities if a.severity == Severity.BORDERLINE]

    if critical:
        st.error("🚨 **Critical Values Detected** — Immediate medical attention may be required")
        for abn in critical:
            st.markdown(
                f'<div class="critical-alert"><b>🚨 {abn.test_name.replace("_", " ").title()}</b>: '
                f'{abn.value} {abn.unit or ""}<br>{abn.message}</div>',
                unsafe_allow_html=True,
            )

    if abnormal:
        st.warning("⚠️ **Abnormal Values Detected**")
        for abn in abnormal:
            conditions_str = ", ".join(abn.possible_conditions[:3]) if abn.possible_conditions else "N/A"
            st.markdown(
                f'<div class="abnormal-alert"><b>⚠️ {abn.test_name.replace("_", " ").title()}</b>: '
                f'{abn.value} {abn.unit or ""}<br>{abn.message}<br>'
                f'<small>Possible conditions: {conditions_str}</small></div>',
                unsafe_allow_html=True,
            )

    if borderline:
        st.info("ℹ️ **Borderline Values**")
        for abn in borderline:
            st.markdown(
                f'<div class="abnormal-alert"><b>ℹ️ {abn.test_name.replace("_", " ").title()}</b>: '
                f'{abn.value} {abn.unit or ""} — {abn.message}</div>',
                unsafe_allow_html=True,
            )

    if not report.abnormalities:
        st.success("✅ All test results are within normal ranges!")

    if st.button("➡️ Start Diagnostic Questions", type="primary", use_container_width=True):
        pipeline.start_elimination()
        st.session_state.current_stage = "questions"
        st.rerun()


def questions_stage():
    st.header("❓ Diagnostic Questions")
    st.markdown("Answer these questions to help narrow down potential diagnoses.")

    pipeline: MedicalRAGPipeline = st.session_state.pipeline
    state = pipeline.session.elimination_state

    if state is None:
        st.error("No elimination state found.")
        return

    # Show active candidates
    active = [c for c in state.candidates if not c.eliminated]
    if active:
        st.subheader("🔬 Conditions Under Investigation")
        for candidate in active[:5]:
            st.progress(candidate.confidence, text=f"{candidate.condition_name}: {candidate.confidence:.0%}")

    st.markdown("---")
    st.subheader("Please answer the following questions:")

    questions = pipeline.get_questions(5)

    if not questions or state.completed:
        st.info("✅ All questions answered! Proceeding to diagnosis.")
        if st.button("➡️ Generate Diagnosis", type="primary", use_container_width=True):
            st.session_state.current_stage = "diagnosis"
            st.rerun()
        return

    answers = {}
    for q in questions:
        st.markdown(
            f'<div class="question-card"><b>{q.question_text}</b></div>',
            unsafe_allow_html=True,
        )
        answer = st.radio(
            f"Answer for: {q.question_id}",
            ["Not answered", "Yes", "No", "Not sure"],
            key=f"radio_{q.question_id}",
            label_visibility="collapsed",
            horizontal=True,
        )
        if answer != "Not answered":
            answers[q.question_id] = answer

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit Answers", type="primary", use_container_width=True):
            if answers:
                pipeline.answer_questions_batch(answers)
                st.rerun()
    with col2:
        if st.button("⏭️ Skip Questions", use_container_width=True):
            pipeline.skip_questions()
            st.session_state.current_stage = "diagnosis"
            st.rerun()

    if state.completed:
        if st.button("➡️ Generate Diagnosis", type="primary", use_container_width=True):
            st.session_state.current_stage = "diagnosis"
            st.rerun()


def diagnosis_stage():
    st.header("🧠 Generating Diagnosis")

    pipeline: MedicalRAGPipeline = st.session_state.pipeline

    with st.spinner("🤖 AI is analyzing your results... This may take a moment."):
        try:
            pipeline.generate_diagnosis()
        except Exception as e:
            st.warning(f"AI diagnosis unavailable ({type(e).__name__}). Using rule-based analysis.")
            if not pipeline.session.diagnosis:
                pipeline.session.diagnosis = pipeline._rule_based_diagnosis()

    with st.spinner("🏥 Finding specialist recommendations..."):
        try:
            pipeline.recommend_specialists()
        except Exception:
            pass

    st.session_state.current_stage = "results"
    st.rerun()


def results_stage():
    st.header("📊 Diagnostic Results")
    pipeline: MedicalRAGPipeline = st.session_state.pipeline

    tab_diag, tab_spec, tab_elim, tab_followup = st.tabs([
        "🧠 Diagnosis", "🏥 Specialist Referrals", "📉 Elimination Process", "💬 Follow-up Questions"
    ])

    with tab_diag:
        if pipeline.session.diagnosis:
            st.markdown(pipeline.session.diagnosis)
        else:
            st.info("No diagnosis available.")

    with tab_spec:
        recs = pipeline.session.specialist_recommendations
        if recs:
            for rec in recs:
                urgency_colors = {"urgent": "🔴", "soon": "🟠", "routine": "🟡", "monitor": "🟢"}
                emoji = urgency_colors.get(rec.urgency, "⬜")
                st.markdown(
                    f'<div class="specialist-card">'
                    f'<b>{emoji} {rec.specialist_title}</b> — {rec.urgency.upper()}<br>'
                    f'{rec.specialist_description}<br>'
                    f'<small>Conditions: {", ".join(rec.conditions)}</small><br>'
                    f'<small>Confidence: {rec.confidence:.0%} | {rec.urgency_description}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No specialist referrals at this time.")

    with tab_elim:
        state = pipeline.session.elimination_state
        if state:
            st.subheader("Diagnostic Candidates")
            active = [c for c in state.candidates if not c.eliminated]
            for c in active:
                st.progress(c.confidence, text=f"{c.condition_name}: {c.confidence:.0%}")

            eliminated = [c for c in state.candidates if c.eliminated]
            if eliminated:
                st.subheader("Eliminated Conditions")
                for c in eliminated:
                    st.markdown(f"❌ **{c.condition_name}**: {c.elimination_reason}")

            answered = [(q.question_text, q.answer) for q in state.questions if q.asked]
            if answered:
                st.subheader("Your Responses")
                for q_text, ans in answered:
                    icon = "✅" if ans == "Yes" else "❌" if ans == "No" else "❓"
                    st.markdown(f"{icon} **Q:** {q_text}\n   **A:** {ans}")

    with tab_followup:
        st.subheader("💬 Ask Follow-up Questions")
        st.markdown("Ask any questions about your results or diagnosis.")
        user_q = st.text_input("Your question:", key="followup_q")
        if st.button("Ask", key="ask_btn") and user_q:
            with st.spinner("Generating answer..."):
                try:
                    answer = pipeline.ask_followup(user_q)
                    st.markdown(f"**Answer:** {answer}")
                except Exception:
                    st.warning("Follow-up questions require a valid API key. Check your OPENAI_API_KEY and OPENAI_BASE_URL in .env.")

    st.markdown("---")
    report_text = pipeline.get_session_summary()
    st.download_button(
        "📥 Download Full Report",
        data=report_text,
        file_name="medical_report.txt",
        mime="text/plain",
        use_container_width=True,
    )


def main():
    init_state()
    render_sidebar()

    stage = st.session_state.current_stage
    if stage == "input":
        input_stage()
    elif stage == "demographics":
        demographics_stage()
    elif stage == "detection":
        detection_stage()
    elif stage == "questions":
        questions_stage()
    elif stage == "diagnosis":
        diagnosis_stage()
    elif stage == "results":
        results_stage()


if __name__ == "__main__":
    main()

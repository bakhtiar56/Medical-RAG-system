"""CLI demo for the Medical RAG system."""

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.rag_pipeline import MedicalRAGPipeline, PatientInfo

console = Console()


def get_sample_test_data() -> dict:
    """Return comprehensive abnormal test data for a 52-year-old male."""
    return {
        "hemoglobin": 10.5,
        "white_blood_cells": 12500,
        "platelets": 420000,
        "red_blood_cells": 3.8,
        "mean_corpuscular_volume": 72,
        "glucose_fasting": 185,
        "creatinine": 1.8,
        "blood_urea_nitrogen": 32,
        "alt": 85,
        "ast": 62,
        "hba1c": 7.8,
        "total_cholesterol": 245,
        "ldl_cholesterol": 165,
        "triglycerides": 210,
        "tsh": 6.2,
    }


def run_demo(interactive: bool = False) -> None:
    """Run the Medical RAG demo."""
    console.print(Panel.fit(
        "[bold blue]🏥 Medical RAG System — Demo[/bold blue]\n"
        "[dim]AI-powered medical laboratory report analysis[/dim]",
        border_style="blue",
    ))

    # Setup
    patient = PatientInfo(age=52, sex="male")
    pipeline = MedicalRAGPipeline()
    pipeline.start_session(patient)

    # Input
    test_data = get_sample_test_data()
    console.print(f"\n[bold]Patient:[/bold] {patient.age}yo {patient.sex}")
    console.print(f"[bold]Tests:[/bold] {len(test_data)} lab values\n")

    table = Table(title="Sample Lab Results", show_header=True)
    table.add_column("Test", style="cyan")
    table.add_column("Value", style="yellow")
    for name, value in test_data.items():
        table.add_row(name.replace("_", " ").title(), str(value))
    console.print(table)

    # Pipeline
    pipeline.input_form(test_data)
    report = pipeline.detect_abnormalities()

    console.print(f"\n[bold]Detection:[/bold] {report.abnormal_count} abnormalities found "
                  f"({report.critical_count} critical)")

    if interactive:
        pipeline.start_elimination()
        questions = pipeline.get_questions(3)
        if questions:
            console.print("\n[bold yellow]Diagnostic Questions:[/bold yellow]")
            from rich.prompt import Prompt
            for q in questions:
                answer = Prompt.ask(f"  {q.question_text}", choices=["Yes", "No", "Not sure"])
                pipeline.answer_question(q.question_id, answer)
    else:
        pipeline.start_elimination()
        pipeline.skip_questions()

    # Diagnosis
    console.print("\n[bold]Generating diagnosis...[/bold]")
    try:
        diagnosis = pipeline.generate_diagnosis()
        console.print(Panel(diagnosis, title="Diagnosis", border_style="green"))
    except Exception as e:
        console.print(f"[yellow]AI diagnosis unavailable: {type(e).__name__}[/yellow]")
        diagnosis = pipeline._rule_based_diagnosis()
        console.print(Panel(diagnosis, title="Rule-based Analysis", border_style="yellow"))

    # Specialists
    recs = pipeline.recommend_specialists()
    if recs:
        console.print("\n[bold]Specialist Referrals:[/bold]")
        for rec in recs:
            emoji = {"urgent": "🔴", "soon": "🟠", "routine": "🟡", "monitor": "🟢"}.get(rec.urgency, "⬜")
            console.print(f"  {emoji} {rec.specialist_title} ({rec.urgency})")


def main():
    parser = argparse.ArgumentParser(description="Medical RAG System Demo")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive Q&A mode")
    args = parser.parse_args()
    run_demo(interactive=args.interactive)


if __name__ == "__main__":
    main()

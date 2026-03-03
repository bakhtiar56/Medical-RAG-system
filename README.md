# 🏥 MedDiag AI — Medical RAG System

![Python](https://img.shields.io/badge/python-3.11-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.2.16-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.5-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37.1-red)
![License](https://img.shields.io/badge/license-MIT-blue)

An AI-powered Medical RAG (Retrieval-Augmented Generation) system that analyzes medical laboratory reports (blood, urine, stool) and provides diagnostic assessments using a **process-of-elimination** approach — mimicking how a doctor arrives at a diagnosis by asking targeted questions and narrowing down conditions.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📋 Multi-format Input | PDF reports, plain text, or manual form entry |
| 🔍 Abnormality Detection | Demographic-aware detection with CRITICAL/ABNORMAL/BORDERLINE severity |
| ❓ Elimination Engine | Doctor-like Q&A to narrow down diagnoses |
| 🧠 LLM Diagnosis | GPT-4o powered comprehensive diagnostic reports |
| 🏥 Specialist Referrals | Urgency-ranked specialist recommendations |
| 🌐 API Enrichment | OpenFDA, NIH MedlinePlus, Disease Ontology integration |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE (Streamlit)                 │
│  Upload Reports → Answer Questions → Get Diagnosis & Referral  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   ORCHESTRATION LAYER (LangChain)               │
│  Report Parser → Abnormality Detector → Diagnostic Reasoner    │
└───────┬──────────────────────┬──────────────────────┬───────────┘
        │                      │                      │
┌───────▼───────┐  ┌───────────▼──────────┐  ┌───────▼───────────┐
│  VECTOR DB    │  │  MEDICAL KNOWLEDGE   │  │  ELIMINATION      │
│  (ChromaDB)   │  │  BASE (Structured)   │  │  ENGINE           │
└───────────────┘  └──────────────────────┘  └───────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
git clone https://github.com/bakhtiar56/Medical-RAG-system.git
cd Medical-RAG-system
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run the Web App

```bash
streamlit run app/streamlit_app.py
```

### Run CLI Demo

```bash
python scripts/demo.py
python scripts/demo.py --interactive  # Q&A mode
```

## 🧪 Supported Tests

### Blood Tests
Hemoglobin, WBC, Platelets, RBC, MCV, Fasting Glucose, Creatinine, BUN, ALT, AST, HbA1c, Total Cholesterol, LDL, Triglycerides, TSH, Free T4

### Urine Tests
Protein, Glucose, Blood, pH, Specific Gravity, Ketones, Leukocyte Esterase, Nitrites

### Stool Tests
Fecal Occult Blood, pH, Fat, Calprotectin, WBC, Culture, Ova & Parasites

## 📁 Project Structure

```
medical-rag-system/
├── data/knowledge_base/    # JSON medical knowledge files
├── src/                    # Core Python modules
├── app/streamlit_app.py    # Web UI
├── scripts/                # CLI tools
└── tests/                  # Test suite
```

## 🛠️ Development

```bash
make install      # Install dependencies
make test         # Run tests
make test-cov     # Run tests with coverage
make run          # Start Streamlit app
make demo         # Run CLI demo
make enrich       # Enrich knowledge base from APIs
```

## 🌐 API Integrations

| API | Purpose | Auth Required |
|-----|---------|---------------|
| OpenAI GPT-4o | LLM diagnosis generation | Yes |
| OpenFDA | Drug adverse events | No |
| NIH MedlinePlus | Patient education | No |
| Disease Ontology | Disease classification | No |

## ⚠️ Disclaimer

This system is for **educational and research purposes only**. It does not constitute medical advice and should not replace consultation with qualified healthcare professionals. Always seek professional medical advice for health concerns.

## 👤 Author

**bakhtiar56** — [GitHub](https://github.com/bakhtiar56)

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

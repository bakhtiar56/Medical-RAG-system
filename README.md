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
- OpenAI API key (or compatible provider such as OpenRouter)

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

## 🐳 Docker

The Docker image runs in **API-required mode only** — it will exit immediately with a clear error if `OPENAI_API_KEY` is not provided.

### Required environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | Your OpenAI (or OpenRouter) API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Override for OpenRouter or other compatible APIs |
| `LLM_MODEL` | No | `gpt-4o` | Model used for diagnosis generation |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Model used for embeddings |

### Build

```bash
docker build -t medical-rag-system .
# or
make docker-build
```

### Run

```bash
# Recommended: pass credentials via .env file
docker run -p 8501:8501 --env-file .env medical-rag-system

# Or pass the key directly
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... medical-rag-system
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

If `OPENAI_API_KEY` is missing or empty the container exits immediately:

```
ERROR: OPENAI_API_KEY is not set.
Please provide it via --env-file .env or -e OPENAI_API_KEY=<your-key>.
```

### Docker Compose

```bash
make docker-run    # docker-compose up -d
make docker-stop   # docker-compose down
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
make install        # Install runtime dependencies
make install-dev    # Install runtime + dev/test dependencies (pytest, pytest-cov)
make test           # Run tests (requires install-dev)
make test-cov       # Run tests with coverage
make run            # Start Streamlit app
make demo           # Run CLI demo
make enrich         # Enrich knowledge base from APIs
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

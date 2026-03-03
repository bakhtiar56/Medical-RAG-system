from setuptools import setup, find_packages

setup(
    name="medical-rag-system",
    version="1.0.0",
    author="bakhtiar56",
    description="AI-powered Medical RAG system for laboratory report analysis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.3.0,<0.4.0",
        "langchain-community>=0.3.0,<0.4.0",
        "langchain-openai>=0.3.0,<0.4.0",
        "openai>=1.86.0,<2.0.0",
        "chromadb>=0.5.0,<1.0.0",
        "pypdf>=4.0.0",
        "pdfplumber>=0.11.0",
        "python-docx>=1.1.0",
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "scikit-learn>=1.5.0",
        "streamlit>=1.37.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.8.0",
        "rich>=13.7.0",
        "requests>=2.31.0",
        "sentence-transformers>=2.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "black>=24.0.0",
            "ruff>=0.4.0",
        ],
    },
)
from setuptools import setup, find_packages

setup(
    name="medical-rag-system",
    version="1.0.0",
    author="bakhtiar56",
    description="AI-powered Medical RAG system for laboratory report analysis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "langchain==0.2.16",
        "langchain-community==0.2.16",
        "langchain-openai==0.1.23",
        "openai==1.44.0",
        "chromadb==0.5.5",
        "pypdf==4.3.1",
        "pdfplumber==0.11.2",
        "python-docx==1.1.2",
        "pandas==2.2.2",
        "numpy==1.26.4",
        "scikit-learn==1.5.1",
        "streamlit==1.37.1",
        "python-dotenv==1.0.1",
        "pydantic==2.8.2",
        "rich==13.7.1",
        "requests>=2.31.0",
    ],
)

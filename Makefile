.PHONY: install test test-cov lint format run demo demo-interactive enrich docker-build docker-run docker-stop clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/ app/ scripts/ tests/ --max-line-length=120

format:
	black src/ app/ scripts/ tests/

run:
	streamlit run app/streamlit_app.py

demo:
	python scripts/demo.py

demo-interactive:
	python scripts/demo.py --interactive

enrich:
	python scripts/enrich_kb.py

enrich-condition:
	python scripts/enrich_kb.py --condition $(CONDITION)

docker-build:
	docker build -t medical-rag-system .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

clean:
	find . -depth -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

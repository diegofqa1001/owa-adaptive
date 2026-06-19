.PHONY: install test demo app api lint clean

install:
	pip install -e ".[all]"

test:
	pytest

demo:
	python scripts/run_demo.py

app:
	streamlit run app/streamlit_app.py

api:
	uvicorn owa_adaptive.api:app --reload

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

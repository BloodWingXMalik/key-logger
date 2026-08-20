PYTHON = python3

.PHONY: install run clean

install:
	pip install -r requirements.txt

run:
	$(PYTHON) app.py

clean:
	rm -rf results/* __pycache__ */__pycache__

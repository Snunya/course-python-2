.PHONY: install samples test coverage lint run

install:
	pip install -r requirements.txt

samples:
	python -m tests.make_fixtures

lint:
	flake8 src tests --max-line-length=80 --max-complexity=7

test: samples
	pytest tests/

coverage: samples
	coverage run --branch -m pytest tests/
	coverage report -m
	coverage html

run:
	python -m src.server

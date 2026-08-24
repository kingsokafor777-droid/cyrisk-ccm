.PHONY: bootstrap fixture lint typecheck test build package-check check

bootstrap:
	python -m pip install -r requirements-dev.txt
	python -m pip install -e ../cyrisk-core
	python -m pip install -e .

fixture:
	PYTHONPATH=src python scripts/build_fixture.py

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy src

test:
	pytest

build:
	python -m pip wheel --no-deps --wheel-dir dist .

package-check: build
	python scripts/check_package.py

check: fixture lint typecheck test package-check

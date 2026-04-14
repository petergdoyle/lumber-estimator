VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

# Find all projects that have a project.yaml
PROJECTS := $(patsubst projects/%/project.yaml,%,$(wildcard projects/*/project.yaml))
PROJECT_TARGETS := $(addprefix project-, $(PROJECTS))

.PHONY: setup run clean test help $(PROJECT_TARGETS)

help:
	@echo "Available commands:"
	@echo "  make setup        - Initialize virtual environment and install dependencies"
	@echo "  make help         - Show this help message"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean virtual environment and caches"
	@echo "  make clean-outputs- Clean generated project artifacts (PDFs, images, etc.)"
	@echo "  make new-project  - Interactively create a new project folder and config"
	@echo "\nAvailable projects:"
	@for p in $(PROJECTS); do \
		echo "  make project-$$p"; \
	done

$(PROJECT_TARGETS): project-%:
	$(PYTHON) -m src.lumber_estimator.cli.main $*

new-project:
	@$(PYTHON) -m src.lumber_estimator.cli.create_project

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	mkdir -p projects
	touch projects/.gitkeep

run:
	$(PYTHON) -m src.lumber_estimator.cli.main

test:
	$(PYTHON) -m pytest

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

clean-outputs:
	@$(PYTHON) -m src.lumber_estimator.cli.clean_outputs

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

serve:
	$(VENV)/bin/uvicorn src.lumber_estimator.web.server:app --reload

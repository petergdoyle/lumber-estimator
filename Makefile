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
	$(PYTHON) src/main.py $*

new-project:
	@$(PYTHON) src/create_project.py

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	mkdir -p projects
	touch projects/.gitkeep

run:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m pytest

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

clean-outputs:
	@echo "Cleaning generated reports and blueprints from all projects..."
	find projects -name "*.pdf" -type f -delete
	find projects -name "*.png" -type f -delete
	find projects -name "buy_report.md" -type f -delete
	find projects -name "estimation_summary.csv" -type f -delete
	find projects -name "purchasing_dimensions.csv" -type f -delete
	find projects -mindepth 2 -type d -name "blueprints*" -exec rm -rf {} + 2>/dev/null || true
	@echo "Done."

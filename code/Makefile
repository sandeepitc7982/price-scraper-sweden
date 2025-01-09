PROJECT_VERSION := $(shell poetry version --short)

help:
	@echo "Usage: make [target]"
	@echo "make bootstrap_local"
	@echo "		Bootstrap local environment"
	@echo "make run_scraper_local"
	@echo "		Run scraper in local environment"
	@echo "make run_finance_scraper_local"
	@echo "		Run finance scraper in local environment"
	@echo "make run_finance_compare_local"
	@echo "		Run finance compare in local environment"
	@echo "make run_compare_local"
	@echo "		Run price compare in local environment"
	@echo "make run_scraper_from_whl"
	@echo "		Run scraper in local environment directly from the  wheel distribution"
	@echo "make run_finance_scraper_from_whl"
	@echo "		Run finance scraper in local environment directly from the  wheel distribution"
	@echo "make run_finance_compare_from_whl"
	@echo "		Run finance comparer in local environment directly from the  wheel distribution"
	@echo "make build-image"
	@echo "		Builds a new docker image\n		Warning: Build Image is not compatible with mac OS"
	@echo "make format"
	@echo "		Format code using black"
	@echo "make check-format"
	@echo "		Check code format using black"
	@echo "make lint"
	@echo "		Test for linters"
	@echo "make lint-xml"
	@echo "		Test for linters and output XML report"
	@echo "make test-unit"
	@echo "		Run project unit tests"
	@echo "make test-e2e"
	@echo "		Run project e2e tests. Filter vendor tests using the VENDOR argument."
.PHONY: help
.DEFAULT: help

bootstrap_local:
	brew install pipx
	pipx install poetry
	#python3 -m pip install poetry # Use this command to install poetry in case the above one fails (Added)
	poetry install
.PHONY: bootstrap_local

##	Running the Scrapers & Comparers Using Poetry
run_scraper_local:
	poetry install
	poetry run price-monitor run-scraper --config-file config/local/config.json
.PHONY: run_scraper_local

run_finance_scraper_local:
	poetry install
	poetry run price-monitor run-finance-scraper --config-file config/local/config.json
.PHONY: run_finance_scraper_local

run_finance_compare_local:
	poetry install
	poetry run price-monitor run-finance-compare --config-file config/local/config.json
.PHONY: run_finance_compare_local


run_compare_local:
	poetry install
	poetry run price-monitor run-compare --config-file config/local/config.json
.PHONY: run_compare_local

run_quality_check:
	poetry install
	poetry run price-monitor check-data-quality --config-file config/local/config.json
.PHONY: run_quality_check

format:
	@poetry run black src/ test/
.PHONY: format

check-format:
	@poetry run black --check --diff src/ test/
.PHONY: check-format

lint:
	@poetry run flake8 src/ test/
.PHONY: lint

lint-xml:
	@poetry run flake8 src/ test/ --output-file=flake8-pricescraper.xml --format junit-xml --exit-zero
.PHONY: lint-xml

test-unit:
	poetry run coverage run -m pytest -m "not cli" && poetry run coverage report -m
.PHONY: test-unit

test-e2e:
	poetry run pytest -m "cli" $(if $(VENDOR), -m $(VENDOR))
.PHONY: test-e2e

install_from_whl:clean
	poetry install
	poetry build
	pip install dist/price_monitor-$(PROJECT_VERSION)-py3-none-any.whl --force-reinstall --ignore-installed
.PHONY: install_from_whl

##	Running the Scrapers & Comparers from the wheel distribution
run_scraper_from_whl: install_from_whl
	price-monitor run-scraper --config-file config/local/config.json
.PHONY: run_scraper_from_whl

run_finance_scraper_from_whl: install_from_whl
	price-monitor run-finance-scraper --config-file config/local/config.json
.PHONY: run_finance_scraper_from_whl

run_finance_compare_from_whl: install_from_whl
	price-monitor run-finance-compare --config-file config/local/config.json
.PHONY: run_finance_compare_from_whl

build-image:
	if [ -e "dist" ]; then rm -r dist; fi
	poetry build
	docker build --platform linux/amd64 -t price-monitor:$(PROJECT_VERSION) -t price-monitor:latest .
.PHONY: build-image

clean:
	@rm -rf dist/ build/ *.egg-info
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -exec rm -rf {} +
	@find . -name '*.pyo' -exec rm -rf {} +
	@rm -rf .venv
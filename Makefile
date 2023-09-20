# To release a new version `make release ver=<args>`
# https://python-poetry.org/docs/cli/#version

CURRENT_BRANCH := $(shell git branch --show-current)

shell:
	poetry install --with dev
	poetry shell

release:
	$(if $(filter $(CURRENT_BRANCH),master),,$(error ERR: Not on master branch))
	$(eval VERSION := $(shell poetry version $(ver) -s))
	@git add pyproject.toml
	@git commit -m "v$(VERSION)"
	@git tag v$(VERSION)
	@git push
	@git push --tags
	@poetry version

release-dry:
	$(if $(filter $(CURRENT_BRANCH),master),,$(warning WARN: Not on master branch))
	$(eval VERSION := $(shell poetry version $(ver) -s --dry-run))
	@echo "Dry run: git add pyproject.toml"
	@echo "Dry run: git tag v$(VERSION)"
	@echo "Dry run: git push"
	@echo "Dry run: git push --tags"
	@echo "Run `make release ver=$(ver)` to release"

lint:
	poetry run pre-commit run --all-files

test:
	poetry run pytest -s
	poetry run mypy

profile:
	poetry run pytest --durations=3

serve-docs:
	@cd docs;\
	make html;\
	cd build/html;\
	python -m http.server;\

serve-coverage:
	@pytest --cov --cov-report=html;\
	cd htmlcov;\
	python -m http.server;\

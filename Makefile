# To release a new version `make release ver=<args>`
# https://python-poetry.org/docs/cli/#version

CURRENT_BRANCH := $(shell git branch --show-current)

shell:
	poetry install --with dev
	poetry shell

release:
	@if [ "$(BRANCH)" != "master" ]; then echo "Not on master branch"; exit 1; fi
	@poetry version $(ver)
	@git add pyproject.toml
	@git commit -m "v$$(poetry version -s)"
	@git tag v$$(poetry version -s)
	@git push
	@git push --tags
	@poetry version


lint:
	poetry run pre-commit run --all-files

test:
	poetry run pytest -s
	poetry run mypy

serve-docs:
	@cd docs;\
	make html;\
	cd build/html;\
	python -m http.server;\

serve-coverage:
	@pytest --cov --cov-report=html;\
	cd htmlcov;\
	python -m http.server;\

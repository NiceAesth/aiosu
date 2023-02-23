# To release a new version `make release ver=<args>`
# https://python-poetry.org/docs/cli/#version

shell:
	poetry install --with dev
	poetry shell

release:
	ifneq ($(shell git rev-parse --abbrev-ref HEAD),master)
		$(error You must be on master branch to release)
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

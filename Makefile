# To release a new version `make release ver=<args>`
# https://python-poetry.org/docs/cli/#version

shell:
	@poetry install --with dev
	@poetry shell

release:
	@poetry version $(ver)
	@git add pyproject.toml
	@git commit -m "v$$(poetry version -s)"
	@git tag v$$(poetry version -s)
	@git push
	@git push --tags
	@poetry version

test:
	@pytest -s
	@mypy

serve-docs:
	@cd docs;\
	make html;\
	cd build/html;\
	python -m http.server;\

serve-coverage:
	@pytest --cov --cov-report=html;\
	cd htmlcov;\
	python -m http.server;\

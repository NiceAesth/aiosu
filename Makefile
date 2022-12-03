# To release a new version `make release ver=<args>`
# https://python-poetry.org/docs/cli/#version

release:
    @poetry version $(ver)
    @git add pyproject.toml
    @git commit -m "v$$(poetry version -s)"
    @git tag v$$(poetry version -s)
    @git push
    @git push --tags
    @poetry version

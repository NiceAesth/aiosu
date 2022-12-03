# To release a new version `make version v=<args>`

version:
    @poetry version $(v)
    @git add pyproject.toml
    @git commit -m "v$$(poetry version -s)"
    @git tag v$$(poetry version -s)
    @git push
    @git push --tags
    @poetry version

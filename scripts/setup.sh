POETRY_VERSION=$(grep -Po '(?<=^requires-poetry\s*=\s*")[0-9]+\.[0-9]+\.[0-9]+(?=")' pyproject.toml)
pip install "poetry==$POETRY_VERSION"
poetry install --no-dev --no-interaction --no-ansi

#!/bin/sh

set -e

exec 1>&2

# formatting
isort --multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=88 --check vulnspec/ tools/ tests/
black --check vulnspec/ tools/ tests/

# type checking
mypy vulnspec/ tools/ tests/

# linting
pylint vulnspec/ tools/ tests/

# simple run
python -m vulnspec --help > /dev/null

# tests
pytest


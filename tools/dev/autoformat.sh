#!/bin/bash

isort \
    --multi-line=3 \
    --trailing-comma \
    --force-grid-wrap=0 \
    --use-parentheses \
    --line-width=88 \
    vulnspec/ tools/ tests/ examples/

black vulnspec/ tools/ tests/ examples/

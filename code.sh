#!/usr/bin/env bash

pip install autoflake yapf isort black autopep8
autopep8 --verbose --in-place --recursive --aggressive --aggressive --ignore=W605 .
autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports .
black .
isort .
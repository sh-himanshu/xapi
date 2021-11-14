#!/usr/bin/env bash

# Run API
if command -v poetry &> /dev/null
then 
    poetry run python -m src
else
    python -m src
fi
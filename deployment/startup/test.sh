#!/bin/bash
pytest --asyncio-mode=auto --cov=/apps/app --cov-config=.coveragerc $ADDITIONAL_COMMANDS -rfE -p no:warnings
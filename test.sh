#!/usr/bin/env bash

PYTHONPATH="$(pwd)/src" py.test --cov-config=./.coveragerc --cov-report=term-missing --cov-branch --cov=./src/ tests/
[[ $? != 0 ]] && echo "Tests failed!" >&2 && exit 1

if [[ -n "${BUILDKITE}" ]]; then
    coveralls
    [[ $? != 0 ]] && echo "Coverage reporting failed!" >&2 && exit 1
fi

exit 0
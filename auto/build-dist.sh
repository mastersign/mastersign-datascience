#!/usr/bin/env bash

# Bash script for building the distribution package

cd "$(dirname $0)/.."
exec python3 setup.py sdist bdist_wheel

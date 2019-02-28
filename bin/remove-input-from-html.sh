#!/usr/bin/env bash
APP_ROOT="$(dirname "$(dirname "$(readlink -fm "$0")")")"
export PYTHONPATH="${APP_ROOT}:${PYTHONPATH}"
exec python3 -m mastersign.datascience.notebook.remove_input_from_html "$@"

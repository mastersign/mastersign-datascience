#!/usr/bin/env bash

# Bash script for building the HTML output of the Sphinx documentation

cd "$(dirname $0)/../doc"
source_dir=source
build_dir=build

function assert_python_cli() {
    command="$1"
    package="$2"
    title="$3"
    url="$4"
    if ! which $1 >/dev/null 2>&1; then
        echo "The command '$command' was not found in PATH."
        echo ""
        echo "Install $title with:"
        echo ""
        echo "pip3 install --user $package"
        echo ""
        echo "Or grab it from $url"
        exit 1
    fi
}

assert_python_cli sphinx-build sphinx Sphinx http://sphinx-doc.org/

if [ "$1" == "" ]; then
    sphinx-build -M help "$source_dir" "$build_dir" $SPHINXOPTS
    echo ""
    echo "NOTE: Replace 'make' with 'auto/doc-build.sh' in this project."
    exit 1
fi

if ! [ -d "$source_dir/_static" ]; then mkdir "$source_dir/_static"; fi
if ! [ -d "$source_dir/_templates" ]; then mkdir "$source_dir/_templates"; fi

exec sphinx-build -M $1 "$source_dir" "$build_dir" $SPHINXOPTS

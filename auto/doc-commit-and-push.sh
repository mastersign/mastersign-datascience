#!/usr/bin/env bash

# Bash script for commiting unstaged changes in Sphinx documentation HTML output
# and pushing subtree to Git branch gh-pages

remote=origin
pages_branch=gh-pages
docs_path=doc/build/html

cd "$(dirname $0)/.."

function assert_command() {
    if ! which $1 >/dev/null 2>&1; then
        echo "The command '$1' was not found in PATH."
        exit 1
    fi
}

assert_command git

git diff --exit-code --cached >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "There are files staged but not commited. Cancelling."
    exit 1
fi

git add "$docs_path"
if [ $? -ne 0 ]; then
    echo "Staging changed docs failed. Cancelling."
    exit 1
fi

git commit -m "updated docs"
if [ $? -ne 0 ]; then
    echo "Committing changed docs failed. Cancelling."
    exit 1
fi

git fetch $remote $pages_branch
if [ $? -ne 0 ]; then
    git subtree push --prefix "$docs_path" $remote $pages_branch
    if [ $? -ne 0 ]; then
        echo "Creating subtree reference failed. Cancelling."
    fi
    exit 0
fi

git subtree split --prefix "$docs_path" --onto $remote/$pages_branch > pages-branch-ref.txt
if [ $? -ne 0 ]; then
    echo "Updating subtree reference failed. Cancelling."
    exit 1
fi
pages_branch_ref="$(cat pages-branch-ref.txt)"
rm pages-branch-ref.txt

git push $remote $pages_branch_ref:$pages_branch
if [ $? -ne 0 ]; then
    echo "Pushing changed docs to branch gh-pages failed."
    exit 1
fi

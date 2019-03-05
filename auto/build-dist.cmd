@ECHO OFF
SETLOCAL

:: CMD script for building the distribution package

PUSHD "%~dp0.."
CALL python3 setup.py sdist bdist_wheel
POPD

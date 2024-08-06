@ECHO OFF
CD "%~dp0"
call python3 setup.py bdist_wheel
call python3 setup.py sdist

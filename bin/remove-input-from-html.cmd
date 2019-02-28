@ECHO OFF
SETLOCAL
SET PYTHONPATH=%~dp0..;%PYTHONPATH%
python -m mastersign.datascience.notebook.remove_input_from_html %*

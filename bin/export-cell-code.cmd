@ECHO OFF
SETLOCAL
SET PYTHONPATH=%~dp0..;%PYTHONPATH%
python -m mastersign.datascience.notebook.export_cell_code %*

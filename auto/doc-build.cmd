@ECHO OFF
SETLOCAL

:: CMD script for building the HTML output of the Sphinx documentation

PUSHD "%~dp0..\doc"
SET SOURCEDIR=source
SET BUILDDIR=build

CALL:ASSERT_COMMAND sphinx-build
IF ERRORLEVEL 1 (
	CALL:PACKAGE_INSTALL_INFO sphinx Sphinx http://sphinx-doc.org/
	GOTO:ERROR
)

IF "%1" == "" GOTO:HELP

IF NOT EXIST "%SOURCEDIR%\_static\" MKDIR "%SOURCEDIR%\_static"
IF NOT EXIST "%SOURCEDIR%\_templates\" MKDIR "%SOURCEDIR%\_templates"

CALL sphinx-build -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
SET STATUS=%ERRORLEVEL%
IF %STATUS% NEQ 0 GOTO:ERROR

GOTO:END

:: PROCEDURES ::

:END
POPD
GOTO:EOF

:ERROR
POPD
EXIT /B %STATUS%

:HELP
CALL sphinx-build -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
ECHO.
ECHO.NOTE: Replace 'make' with 'auto\doc_build.cmd' in this project.
GOTO:END


:ASSERT_COMMAND
SET NAME=%1
WHERE %NAME% >NUL 2>&1
IF ERRORLEVEL 1 (
	ECHO.
	ECHO.The command '%NAME%' was not found in PATH.
	EXIT /B 1
)
GOTO:EOF

:PACKAGE_INSTALL_INFO
SET PACKAGE=%1
SET TITLE=%2
SET URL=%3
ECHO.
ECHO.Install %TITLE% with:
ECHO.
ECHO.pip install %PACKAGE%
ECHO.or
ECHO.pip install --user %PACKAGE%
ECHO.
ECHO.Or grab it from %URL%
GOTO:EOF

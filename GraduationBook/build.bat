@echo off
REM ============================================================
REM  build.bat - compile the LaTeX book to PDF
REM  Finds main.tex in this script's own folder and builds it.
REM  Engine preference: tectonic -> latexmk -> pdflatex
REM ============================================================
setlocal enabledelayedexpansion

REM Work from the folder this script lives in
cd /d "%~dp0"

set "MAIN=main.tex"
if not exist "%MAIN%" (
    echo [ERROR] %MAIN% not found in "%~dp0".
    exit /b 1
)
echo [build] Found %MAIN% in "%CD%"

REM ---- locate a compiler --------------------------------------
set "ENGINE="

where tectonic >nul 2>&1 && set "ENGINE=tectonic"
if not defined ENGINE if exist "C:\tmp\tectonic.exe" set "ENGINE=C:\tmp\tectonic.exe"
if not defined ENGINE where latexmk >nul 2>&1 && set "ENGINE=latexmk"
if not defined ENGINE where pdflatex >nul 2>&1 && set "ENGINE=pdflatex"

if not defined ENGINE (
    echo [ERROR] No LaTeX engine found ^(tectonic, latexmk, or pdflatex^).
    echo         Install one, or upload the folder to Overleaf.
    exit /b 1
)
echo [build] Using engine: %ENGINE%

REM ---- clean stale auxiliary files (deterministic pagination) --
del /q main.aux main.toc main.lof main.lot main.out main.log main.xdv >nul 2>&1
del /q chapters\*.aux >nul 2>&1

REM ---- compile -------------------------------------------------
echo "%ENGINE%" | findstr /i "tectonic" >nul
if %errorlevel%==0 (
    "%ENGINE%" -X compile "%MAIN%" --outdir "%CD%"
    goto :done
)

echo "%ENGINE%" | findstr /i "latexmk" >nul
if %errorlevel%==0 (
    latexmk -pdf -interaction=nonstopmode -halt-on-error "%MAIN%"
    goto :done
)

REM pdflatex: two passes for TOC + cross-references
pdflatex -interaction=nonstopmode -halt-on-error "%MAIN%"
pdflatex -interaction=nonstopmode -halt-on-error "%MAIN%"

:done
if exist "main.pdf" (
    echo [build] SUCCESS -^> "%CD%\main.pdf"
    exit /b 0
) else (
    echo [build] FAILED - main.pdf was not produced. See the log above.
    exit /b 1
)

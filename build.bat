@echo off
setlocal
cd /d "%~dp0"

rem Prefer the Windows "py" launcher, fall back to "python".
set "PY=python"
where py >nul 2>nul && set "PY=py"

echo ============================================
echo    Midnight Dev Toolkit - Build
echo ============================================
echo.
echo    1. Just build (keep current version)
echo    2. Build + bump PATCH   (bug fix)
echo    3. Build + bump MINOR   (new feature)
echo    4. Build + bump MAJOR   (big release)
echo.
set "choice="
set /p "choice=Choose 1-4 (or press Enter for 1): "

if "%choice%"=="2" goto patch
if "%choice%"=="3" goto minor
if "%choice%"=="4" goto major
goto plain

:patch
%PY% build.py --bump patch
goto done
:minor
%PY% build.py --bump minor
goto done
:major
%PY% build.py --bump major
goto done
:plain
%PY% build.py
goto done

:done
echo.
pause

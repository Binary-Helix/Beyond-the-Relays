@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  BtR Patch Compatibility Analyzer — Launcher
::  Place this .bat in the same folder as btr_analyzer.py
:: ============================================================

:: ── CONFIG — edit these paths before running ────────────────

set OLD_VANILLA=E:\Repositories\vanilla_stellaris\install
set NEW_VANILLA=F:\SteamLibrary\steamapps\common\Stellaris
set MOD_DIR=E:\Repositories\btr_skunkworks

:: Version labels — entered at runtime, no editing needed
set /p OLD_LABEL=Enter OLD version label (e.g. 4.23): 
set /p NEW_LABEL=Enter NEW version label (e.g. 4.3openbeta): 

:: ────────────────────────────────────────────────────────────

title BtR Patch Analyzer

echo.
echo  =====================================================
echo   Binary Helix ^| Stellaris Patch Compatibility Tool
echo  =====================================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+ and ensure
    echo          it is added to your PATH.
    echo.
    pause
    exit /b 1
)

:: Check the script exists next to this batch file
set SCRIPT_DIR=%~dp0
set SCRIPT=%SCRIPT_DIR%btr_analyzer.py

if not exist "%SCRIPT%" (
    echo  [ERROR] btr_analyzer.py not found at:
    echo          %SCRIPT%
    echo.
    echo          Place this .bat in the same folder as btr_analyzer.py
    echo.
    pause
    exit /b 1
)

:: Check directories exist
if not exist "%OLD_VANILLA%" (
    echo  [ERROR] OLD vanilla path not found:
    echo          %OLD_VANILLA%
    echo.
    echo          Edit OLD_VANILLA in this batch file, or see --help-versions
    echo          for instructions on downloading the previous Stellaris version.
    echo.
    pause
    exit /b 1
)

if not exist "%NEW_VANILLA%" (
    echo  [ERROR] NEW vanilla path not found:
    echo          %NEW_VANILLA%
    echo.
    pause
    exit /b 1
)

if not exist "%MOD_DIR%" (
    echo  [ERROR] Mod directory not found:
    echo          %MOD_DIR%
    echo.
    echo          Edit MOD_DIR in this batch file to point at your mod folder.
    echo.
    pause
    exit /b 1
)

echo  OLD vanilla : %OLD_VANILLA%
echo  NEW vanilla : %NEW_VANILLA%
echo  Mod dir     : %MOD_DIR%
echo  Output      : (auto-named from version labels)
echo.

python "%SCRIPT%" ^
    --old   "%OLD_VANILLA%" ^
    --new   "%NEW_VANILLA%" ^
    --mod   "%MOD_DIR%"     ^
    --old-label "%OLD_LABEL%" ^
    --new-label "%NEW_LABEL%"

if errorlevel 1 (
    echo.
    echo  [ERROR] Analyzer exited with an error. See output above.
    echo.
    pause
    exit /b 1
)

echo.
echo  Done! Opening report...
echo.

start "" "%SCRIPT_DIR%."

pause

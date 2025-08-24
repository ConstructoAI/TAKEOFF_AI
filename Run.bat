@echo off
echo ========================================
echo   CONSTRUCTO AI 3.0 - ESTIMATEUR IA
echo ========================================
echo.

echo Recherche de Python...

REM Essayer python dans le PATH
python --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

REM Essayer py launcher
py --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found_python
)

REM Essayer python3
python3 --version 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

echo.
echo ========================================
echo ERREUR: Python n'est pas trouve
echo ========================================
echo.
echo SOLUTIONS:
echo 1. Installez Python depuis https://python.org
echo 2. Cochez "Add Python to PATH" pendant l'installation
echo 3. Redemarrez votre ordinateur
echo.
echo OU desactivez les alias Microsoft Store:
echo Parametres Windows ^> Applications ^> Aliases d'execution
echo Desactivez python.exe et python3.exe
echo.
pause
exit /b 1

:found_python
echo Python trouve: %PYTHON_CMD%
%PYTHON_CMD% --version

echo.
echo Installation des dependances...
%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Demarrage de Constructo AI...
echo Interface accessible sur: http://localhost:8501
echo Fermez cette fenetre pour arreter l'application
echo.

%PYTHON_CMD% -m streamlit run app.py

echo.
pause
@echo off
cd /d "%~dp0"
set VENV_DIR=venv
set REQUIREMENTS=requirements.txt
set SCRIPT=app.py

REM Création du venv si nécessaire
if not exist %VENV_DIR% (
    echo Création de l'environnement virtuel...
    python -m venv %VENV_DIR%
)

REM Activation du venv
call %VENV_DIR%\Scripts\activate

REM Installation/MàJ des dépendances
if exist %REQUIREMENTS% (
    echo Vérification des mises à jour des dépendances...
    pip install --upgrade pip
    python.exe -m pip install --upgrade pip
    pip install torch==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
    pip install -r %REQUIREMENTS%
)



REM Lancer le script Python (un tunnel public sera créé)
python %SCRIPT%

REM Désactiver le venv
deactivate

pause

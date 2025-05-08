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
    pip install torch==2.5.1+cpu
    pip install -r %REQUIREMENTS%
)

REM **Activer le partage public Gradio**
set GRADIO_SHARE=True

REM Lancer le script Python (un tunnel public sera créé)
python %SCRIPT%

REM Désactiver le venv
deactivate

pause

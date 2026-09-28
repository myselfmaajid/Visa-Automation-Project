@echo off
title GVC Visa Appointment Bot Launcher
echo =========================================================
echo GVC VISA APPOINTMENT BOT - AUTOMATED LAUNCHER
echo =========================================================
echo.

:: 1. Virtual Environment (venv) Check & Create
if not exist "venv" (
    echo [1/4] Virtual Environment nahi mila. Naya 'venv' banaya ja raha hai...
    python -m venv venv
    echo Virtual Environment kamyabi se ban gaya!
) else (
    echo [1/4] Virtual Environment pehle se majood hai.
)
echo.

:: 2. Activate Virtual Environment
echo [2/4] Virtual Environment ko Activate kiya ja raha hai...
call venv\Scripts\activate.bat
echo Environment Activated!
echo.

:: 3. Requirements Check & Install
if exist "requirements.txt" (
    echo [3/4] Required Libraries check aur install ki ja rahi hain...
    pip install -r requirements.txt --quiet --no-warn-script-location
    echo Saari Libraries Ready hain!
) else (
    echo Requirements file nahi mili! Skipped.
)
echo.

:: 4. Streamlit App Run
echo [4/4] Streamlit Application Start ho rahi hai...
echo.
streamlit run app.py

pause
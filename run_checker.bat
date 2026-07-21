@echo off
echo ===========================================
echo Lancement du bot Facebook AdsPower...
echo ===========================================

IF NOT EXIST "venv" (
    echo [1/3] Creation de l'environnement virtuel...
    python -m venv venv
)

echo [2/3] Activation et installation des dependances...
call venv\Scripts\activate
pip install requests gspread oauth2client selenium

echo [3/3] Lancement du script...
python check_fb_bans.py

echo.
pause

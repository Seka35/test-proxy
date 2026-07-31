@echo off
echo ===================================================
echo     COMPILATION DU PROGRAMME EN .EXE
echo ===================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv venv
) ELSE (
    echo [1/4] Environnement virtuel deja existant.
)

echo [2/4] Activation et installation des dependances...
call venv\Scripts\activate

REM Installation des dependances du projet + customtkinter + pyinstaller
pip install requests gspread oauth2client selenium customtkinter pyinstaller

echo.
echo [3/4] Compilation avec PyInstaller...
echo Cela peut prendre quelques minutes, merci de patienter...
echo.

REM Compilation en un seul fichier (.exe) sans console (--noconsole)
REM --collect-all customtkinter est necessaire pour inclure les themes et polices
pyinstaller --noconsole --onefile --name "Facebook_Checker" --collect-all customtkinter gui_checker.py

echo.
echo [4/4] Nettoyage des fichiers temporaires de compilation...
rmdir /s /q build
del /q Facebook_Checker.spec

echo.
echo ===================================================
echo ✅ COMPILATION TERMINEE AVEC SUCCES !
echo ===================================================
echo Ton fichier .exe se trouve dans le dossier "dist".
echo N'oublie pas de placer le fichier "credentials.json"
echo dans le meme dossier que l'application avant de la lancer.
echo ===================================================
pause

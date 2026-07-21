#!/bin/bash
echo "==========================================="
echo "Lancement du bot Facebook AdsPower..."
echo "==========================================="

if [ ! -d "venv" ]; then
    echo "[1/3] Création de l'environnement virtuel..."
    python3 -m venv venv
fi

echo "[2/3] Activation et installation des dépendances..."
source venv/bin/activate
pip install requests gspread oauth2client selenium

echo "[3/3] Lancement du script..."
python3 check_fb_bans.py

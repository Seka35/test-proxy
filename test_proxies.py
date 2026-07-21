#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de vérification automatique de proxies depuis Google Sheets.
Met à jour les colonnes E (latence), F (qualité), G (date/heure du check).
"""

import time
import concurrent.futures
import requests
from requests.exceptions import ProxyError, ConnectTimeout, ReadTimeout
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ============================================================
#  CONFIGURATION – À MODIFIER SELON TES BESOINS
# ============================================================

# Chemin vers le fichier JSON de ton compte de service
CREDENTIALS_FILE = "credentials.json"

# ⚠️ REMPLACE CET ID PAR CELUI DE TON GOOGLE SHEET
# (ex: https://docs.google.com/spreadsheets/d/1ABC123xyz789/edit → ID = "1ABC123xyz789")
SHEET_ID = "1QEpqh1fZhL0rhMvHfmH_6q5GFTQgJFxUH4ablG9c5Hs"   # <--- METS LE BON ID ICI

# Nom de la feuille (onglet) – par défaut "Feuille 1"
WORKSHEET_NAME = "Suivi des proxys"

# Délai maximum d'attente pour un proxy (secondes)
TIMEOUT = 10

# Nombre de proxies testés en parallèle (ajuste selon la puissance de ton VPS)
THREADS = 50

# URLs de test (si la première échoue, il teste la suivante)
TEST_URLS = [
    "http://api.ipify.org",
    "http://ident.me",
    "http://icanhazip.com"
]

# Seuils de qualité (en millisecondes)
SEUIL_PREMIUM = 800
SEUIL_CORRECT = 1500

# Configuration Telegram
TELEGRAM_BOT_TOKEN = "8825297135:AAHO28B34QLjwI-hwjnpv1W2i7dw8dD13ZQ"
TELEGRAM_CHAT_ID = "-1003924268016"  # <--- METS L'ID DU GROUPE ICI (ex: -100123456789)

# ============================================================

def get_quality(latency_ms):
    """Retourne la pastille qualité selon la latence."""
    if latency_ms < SEUIL_PREMIUM:
        return "🟢 Premium"
    elif latency_ms < SEUIL_CORRECT:
        return "🟡 Correct"
    else:
        return "🔴 Lent"

def send_telegram_report(message, file_path=None):
    """Envoie un rapport via Telegram, avec un fichier optionnel"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Configuration Telegram manquante (Bot token ou Chat ID). Rapport non envoyé.")
        return
        
    if file_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": message,
            "parse_mode": "Markdown"
        }
        try:
            with open(file_path, "rb") as f:
                files = {"document": f}
                response = requests.post(url, data=payload, files=files, timeout=20)
            if response.status_code == 200:
                print("📤 Rapport et fichier Telegram envoyés avec succès.")
            else:
                print(f"⚠️ Erreur lors de l'envoi Telegram : {response.text}")
        except Exception as e:
            print(f"⚠️ Exception lors de l'envoi Telegram : {e}")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("📤 Rapport Telegram envoyé avec succès.")
            else:
                print(f"⚠️ Erreur lors de l'envoi Telegram : {response.text}")
        except Exception as e:
            print(f"⚠️ Exception lors de l'envoi Telegram : {e}")

def test_proxy(proxy_string):
    """
    Teste un proxy unique.
    Retourne (proxy_string, statut, latence_ms, qualité)
    """
    proxy_string = proxy_string.strip()
    if not proxy_string:
        return (proxy_string, "CUT", "0", "CUT")

    try:
        ip, port, user, pwd = proxy_string.split(":")
        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
        proxies = {"http": proxy_url, "https": proxy_url}

        # On teste chaque URL de la liste, si une marche, le proxy est bon
        for url in TEST_URLS:
            start = time.time()
            try:
                response = requests.get(
                    url,
                    proxies=proxies,
                    timeout=TIMEOUT,
                    allow_redirects=False
                )
                elapsed_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    quality = get_quality(elapsed_ms)
                    return (proxy_string, "ON", str(elapsed_ms), quality)
            except Exception:
                # Si ça rate sur cette URL, on passe à la suivante
                continue
                
        # Si on arrive ici, toutes les URLs ont échoué
        return (proxy_string, "CUT", "0", "CUT")

    except Exception:
        # En cas d'erreur de formatage du proxy, etc.
        return (proxy_string, "CUT", "0", "CUT")

def main():
    print("🔐 Connexion à Google Sheets...")
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    except Exception as e:
        print(f"❌ Erreur de connexion à Google Sheets : {e}")
        return

    # Lecture de toutes les lignes
    all_values = sheet.get_all_values()
    if len(all_values) < 2:
        print("❌ La feuille est vide ou ne contient que l'en-tête.")
        return

    # Les proxies sont dans la colonne A (index 0) à partir de la ligne 2
    proxies_to_test = []
    for i, row in enumerate(all_values[1:], start=2):
        if row and row[0].strip() != "":
            proxy_id = row[2].strip() if len(row) > 2 else "Sans_ID"
            proxies_to_test.append((i, row[0].strip(), proxy_id))

    print(f"🔍 {len(proxies_to_test)} proxies trouvés dans la feuille.")

    if not proxies_to_test:
        print("⚠️ Aucun proxy à tester.")
        return

    def test_proxy_with_index(item):
        row_idx, p_string, proxy_id = item
        return row_idx, proxy_id, test_proxy(p_string)

    # Test en parallèle
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_proxy = {executor.submit(test_proxy_with_index, item): item for item in proxies_to_test}
        count = 0
        for future in concurrent.futures.as_completed(future_to_proxy):
            count += 1
            if count % 50 == 0:
                print(f"📊 Progression : {count}/{len(proxies_to_test)} traités...")
            results.append(future.result())

    # Préparation de la mise à jour (batch)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = []
    
    proxies_premium = 0
    proxies_correct = 0
    proxies_lent = 0
    proxies_cut = 0
    proxies_cut_list = []

    for row_index, proxy_id, (orig, status, latency, quality) in results:
        if status == "ON":
            if "Premium" in quality:
                proxies_premium += 1
            elif "Correct" in quality:
                proxies_correct += 1
            else:
                proxies_lent += 1
        else:
            proxies_cut += 1
            proxies_cut_list.append(f"{proxy_id} - {orig}")
        # Mettre à jour la ligne exacte correspondante pour chaque proxy
        # Colonnes E, F, G = indices 5, 6, 7 (1-based)
        updates.append({
            'range': f'E{row_index}:G{row_index}',
            'values': [[f"{latency} ms", quality, now]]
        })

    # Envoi d'une seule requête batch pour mettre à jour toutes les lignes
    try:
        sheet.batch_update(updates)
        print(f"✅ Mise à jour terminée pour {len(results)} proxies.")
        print(f"🕒 Dernier check : {now}")
        
        # Envoi du rapport Telegram
        report_msg = (
            f"📊 *Rapport de vérification des Proxies*\n"
            f"🟢 Premium : {proxies_premium}\n"
            f"🟡 Correct : {proxies_correct}\n"
            f"🔴 Lent : {proxies_lent}\n"
            f"❌ Hors ligne (CUT) : {proxies_cut}\n"
            f"🔄 Total testés : {len(results)}\n"
            f"🕒 Heure du check : {now}"
        )
        
        if proxies_cut_list:
            file_name = "proxies_cut.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("\n".join(proxies_cut_list))
            send_telegram_report(report_msg, file_path=file_name)
        else:
            send_telegram_report(report_msg)
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du sheet : {e}")

if __name__ == "__main__":
    main()
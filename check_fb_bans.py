import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ================= CONFIGURATION =================
CREDS_FILE = 'credentials.json'
SHEET_ID = '1QEpqh1fZhL0rhMvHfmH_6q5GFTQgJFxUH4ablG9c5Hs'
WORKSHEET_NAME = 'Suivi des proxys'
ADS_API = "http://127.0.0.1:50325/api/v1"
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
THREADS = 4  # Nombre de navigateurs à ouvrir en même temps
TELEGRAM_BOT_TOKEN = "8825297135:AAHO28B34QLjwI-hwjnpv1W2i7dw8dD13ZQ"
TELEGRAM_CHAT_ID = "-1003924268016"
# =================================================

from datetime import datetime

def send_telegram_report(message, file_path=None):
    if file_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message, 'parse_mode': 'Markdown'}
                requests.post(url, data=data, files=files)
        except Exception as e:
            print(f"Exception Telegram Document: {e}")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Exception Telegram Message: {e}")

def get_adspower_profiles():
    print("⏳ Récupération de tous les profils AdsPower (cela peut prendre quelques secondes)...")
    profiles = {}
    page = 1
    page_size = 500
    
    while True:
        try:
            resp = requests.get(f"{ADS_API}/user/list?page={page}&page_size={page_size}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    list_data = data.get("data", {}).get("list", [])
                    if not list_data:
                        break # Plus aucun profil à récupérer
                    
                    for p in list_data:
                        proxy_config = p.get("user_proxy_config", {})
                        proxy_ip = proxy_config.get("proxy_host", "").strip()
                        
                        if proxy_ip:
                            profiles[proxy_ip] = {
                                "user_id": p.get("user_id"),
                                "name": p.get("name"),           # ND 31 du 18/07/26
                                "account_name": p.get("password") # VLteam16032026
                            }
                    page += 1
                else:
                    print(f"❌ Erreur API: {data.get('msg')}")
                    break
            else:
                break
        except Exception as e:
            print(f"❌ Erreur de connexion à AdsPower: {e}")
            break
            
    print(f"✅ {len(profiles)} profils indexés avec succès.")
    return profiles

def check_facebook_status(user_id):
    """ Ouvre le profil, check FB, et ferme le profil. """
    # 1. Démarrer le navigateur
    start_url = f"{ADS_API}/browser/start?user_id={user_id}"
    resp = requests.get(start_url)
    
    if resp.status_code != 200 or resp.json().get("code") != 0:
        return "Erreur Lancement"
    
    data = resp.json().get("data", {})
    debugger_address = data.get("ws", {}).get("selenium")
    webdriver_path = data.get("webdriver")
    
    if not debugger_address or not webdriver_path:
        return "Erreur Driver"
        
    status = "Inconnu"
    driver = None
    
    # 2. Se connecter avec Selenium
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)
        
        service = Service(executable_path=webdriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 3. Naviguer vers Facebook
        driver.get("https://www.facebook.com/")
        time.sleep(5) # Attendre que la page charge complètement
        
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()
        
        # 4. Analyser le statut
        if "checkpoint" in current_url or "suspended" in current_url:
            status = "Checkpoint"
        elif "account disabled" in page_source or "compte désactivé" in page_source:
            status = "Banni"
        elif "login" in current_url or "se connecter" in page_source:
            status = "Déconnecté"
        else:
            status = "Actif"
            
    except Exception as e:
        status = "Erreur Selenium"
    finally:
        # 5. Fermer l'onglet (optionnel) et le profil AdsPower
        if driver:
            try:
                driver.quit()
            except:
                pass
        # Ordre à AdsPower de fermer le profil
        requests.get(f"{ADS_API}/browser/stop?user_id={user_id}")
        
    return status

import concurrent.futures

def process_profile(i, fb_id, p_data):
    user_id = p_data["user_id"]
    profile_name = p_data["name"]
    account_name = p_data["account_name"]
    
    print(f"[{i}] 🔍 Démarrage : {fb_id} ({profile_name})...")
    status = check_facebook_status(user_id)
    print(f"[{i}] ➔ Résultat : {status} ({fb_id})")
    
    return {
        'fb_id': fb_id,
        'status': status,
        'account_name': account_name,
        'profile_name': profile_name,
        'update_dict': {
            'range': f'H{i}:J{i}',
            'values': [[status, account_name, profile_name]]
        }
    }

def main():
    print("🚀 Démarrage du robot vérificateur de comptes Facebook...")
    
    # Connexion Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    
    # Charger les profils AdsPower en mémoire
    profiles = get_adspower_profiles()
    if not profiles:
        print("Aucun profil trouvé, arrêt du script.")
        return
        
    print("📊 Lecture du Google Sheet...")
    records = sheet.get_all_values()
    
    tasks = []
    # On va parcourir chaque ligne à partir de la ligne 2
    for i, row in enumerate(records[1:], start=2):
        if not row or len(row) < 3:
            continue
            
        proxy_string = str(row[0]).strip() # Colonne A
        fb_id = str(row[2]).strip()        # Colonne C (pour l'affichage et Google Sheet)
        
        if not proxy_string or not fb_id or fb_id.lower() == "sans_id":
            continue
            
        # Extraire l'IP (avant le premier deux-points)
        sheet_ip = ""
        if ":" in proxy_string:
            sheet_ip = proxy_string.split(":")[0].strip()
        else:
            sheet_ip = proxy_string
            
        if sheet_ip and sheet_ip in profiles:
            tasks.append((i, fb_id, profiles[sheet_ip]))
            
    print(f"⚡ {len(tasks)} profils à vérifier. Lancement de {THREADS} navigateurs en parallèle...")
    
    updates = []
    results_data = []
    # Lancement du multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(process_profile, i, fb_id, p_data) for i, fb_id, p_data in tasks]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    updates.append(result['update_dict'])
                    results_data.append(result)
            except Exception as e:
                print(f"❌ Erreur thread: {e}")
                
    # Mise à jour globale Google Sheets
    if updates:
        print("💾 Sauvegarde de tous les résultats dans Google Sheets en une seule fois...")
        # Pour éviter l'erreur de payload trop lourd, on met à jour par blocs de 100
        for chunk in [updates[x:x+100] for x in range(0, len(updates), 100)]:
            try:
                sheet.batch_update(chunk)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour par lot: {e}")
        print("✅ Terminé avec succès !")
        
        # =================================================
        # Génération et Envoi du Rapport Telegram
        # =================================================
        print("🚀 Préparation du rapport Telegram...")
        actif_count = sum(1 for r in results_data if r['status'] == 'Actif')
        checkpoint_count = sum(1 for r in results_data if r['status'] == 'Checkpoint')
        banni_count = sum(1 for r in results_data if r['status'] == 'Banni')
        erreur_count = sum(1 for r in results_data if r['status'] not in ['Actif', 'Checkpoint', 'Banni'])
        
        issues_list = []
        for r in results_data:
            st = r['status']
            if st != 'Actif':
                if st == "Checkpoint":
                    pastille = "🟡 CHECKPOINT"
                elif st == "Banni":
                    pastille = "🔴 BANNI"
                else:
                    pastille = f"⚪ ERREUR ({st})"
                issues_list.append(f"[{pastille}] FB: {r['fb_id']} | Compte: {r['account_name']} | Profil: {r['profile_name']}")
                
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_msg = (
            f"📊 *Rapport de vérification Facebook (AdsPower)*\n\n"
            f"🟢 Actif : {actif_count}\n"
            f"🟡 Checkpoint : {checkpoint_count}\n"
            f"🔴 Banni : {banni_count}\n"
            f"⚪ Erreur : {erreur_count}\n\n"
            f"🔄 Total vérifiés : {len(results_data)}\n"
            f"🕒 Heure : {now}"
        )
        
        file_name = None
        if issues_list:
            file_name = "fb_issues.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("LISTE DES COMPTES À VÉRIFIER (CHECKPOINT / BANNI / ERREUR)\n")
                f.write("============================================================\n\n")
                f.write("\n".join(issues_list))
                
        send_telegram_report(report_msg, file_path=file_name)
        print("✅ Rapport Telegram envoyé dans le groupe !")
    else:
        print("Aucune mise à jour à faire.")

if __name__ == "__main__":
    main()

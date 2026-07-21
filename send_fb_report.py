import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime

# ================= CONFIGURATION =================
CREDS_FILE = 'credentials.json'
SHEET_ID = '1QEpqh1fZhL0rhMvHfmH_6q5GFTQgJFxUH4ablG9c5Hs'
WORKSHEET_NAME = 'Suivi des proxys'
TELEGRAM_BOT_TOKEN = "8825297135:AAHO28B34QLjwI-hwjnpv1W2i7dw8dD13ZQ"
TELEGRAM_CHAT_ID = "-1003924268016"
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# =================================================

def send_telegram_report(message, file_path=None):
    if file_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message, 'parse_mode': 'Markdown'}
                response = requests.post(url, data=data, files=files)
                if response.status_code != 200:
                    print(f"Erreur Telegram Document: {response.text}")
        except Exception as e:
            print(f"Exception Telegram Document: {e}")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"Erreur Telegram Message: {response.text}")
        except Exception as e:
            print(f"Exception Telegram Message: {e}")

def main():
    print("Récupération des données du Google Sheet...")
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    
    records = sheet.get_all_values()
    
    actif_count = 0
    checkpoint_count = 0
    banni_count = 0
    erreur_count = 0
    
    issues_list = []
    
    # Lecture depuis la ligne 2
    for row in records[1:]:
        if len(row) < 8: # Il faut au moins 8 colonnes pour avoir le statut en H
            continue
            
        fb_id = str(row[2]).strip()
        
        # Gestion si les colonnes I et J sont vides
        status = str(row[7]).strip() if len(row) > 7 else ""
        account_name = str(row[8]).strip() if len(row) > 8 else "Inconnu"
        profile_name = str(row[9]).strip() if len(row) > 9 else "Inconnu"
        
        if not fb_id or fb_id.lower() == "sans_id":
            continue
            
        if not status:
            continue
            
        if status == "Actif":
            actif_count += 1
        elif status == "Checkpoint":
            checkpoint_count += 1
            issues_list.append(f"[🟡 CHECKPOINT] FB: {fb_id} | Compte: {account_name} | Profil: {profile_name}")
        elif status == "Banni":
            banni_count += 1
            issues_list.append(f"[🔴 BANNI] FB: {fb_id} | Compte: {account_name} | Profil: {profile_name}")
        else: # Erreurs Selenium / Lancement
            erreur_count += 1
            issues_list.append(f"[⚪ ERREUR] FB: {fb_id} | Compte: {account_name} | Profil: {profile_name} -> {status}")
            
    total = actif_count + checkpoint_count + banni_count + erreur_count
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_msg = (
        f"📊 *Rapport de vérification Facebook*\n\n"
        f"🟢 Actif : {actif_count}\n"
        f"🟡 Checkpoint : {checkpoint_count}\n"
        f"🔴 Banni : {banni_count}\n"
        f"⚪ Erreur : {erreur_count}\n\n"
        f"🔄 Total vérifiés : {total}\n"
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
    print("✅ Rapport envoyé sur Telegram avec succès !")

if __name__ == "__main__":
    main()

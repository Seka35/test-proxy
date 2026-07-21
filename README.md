# 🚀 Guide d'Utilisation : Vérificateur de Comptes Facebook (AdsPower)

Ce document explique comment configurer et lancer le script de vérification des statuts des comptes Facebook (`check_fb_bans.py`). 

⚠️ **IMPORTANT** : Contrairement au script de vérification des proxies qui tourne sur le VPS, **ce script doit impérativement être lancé sur un ordinateur local (PC/Mac) sur lequel le logiciel AdsPower est installé et en cours d'exécution.**

---

## 🛠️ 1. Prérequis

1. **Cloner ce dépôt** sur votre machine :
   ```bash
   git clone https://github.com/Seka35/test-proxy.git
   cd test-proxy
   ```
2. **Python 3** doit être installé sur la machine.
3. **Activer l'API Locale d'AdsPower** :
   - Ouvrez AdsPower.
   - Allez dans **Paramètres (Settings)** -> **API locale**.
   - Cochez la case pour l'activer.
   - Notez le port affiché (généralement `50325`).
   - Assurez-vous qu'AdsPower reste ouvert et connecté à votre compte avant de lancer le script.

---

## 🔑 2. Configuration des accès Google Sheets (`credentials.json`)

Le script lit et met à jour un fichier Google Sheets. Pour des raisons de sécurité, vous devez générer votre propre fichier d'authentification (`credentials.json`) via Google Cloud Console.

### Étapes pour générer le fichier :

1. Rendez-vous sur la [Google Cloud Console](https://console.cloud.google.com/).
2. Créez un nouveau projet (ou utilisez un projet existant).
   *(Note : S'il demande une organisation, sélectionnez **"Aucune organisation"** ou "No organization" dans le champ Emplacement/Location).*
3. Allez dans **API et services > Bibliothèque**.
4. Cherchez et **Activez** ces deux APIs :
   - `Google Sheets API`
   - `Google Drive API`
5. Allez dans **API et services > Identifiants**.
6. Cliquez sur **Créer des identifiants** > **Compte de service**.
7. Donnez un nom au compte de service (ex: `adspower-bot`) et cliquez sur **Créer et continuer**, puis sur **Terminer**.
8. Dans la liste des comptes de service, cliquez sur celui que vous venez de créer (l'adresse email qui ressemble à `nom@projet.iam.gserviceaccount.com`).
9. Allez dans l'onglet **Clés** > **Ajouter une clé** > **Créer une clé**.
10. Choisissez le format **JSON** et cliquez sur **Créer**. Un fichier va se télécharger sur votre ordinateur.
11. **Renommez ce fichier en `credentials.json`** et placez-le dans le même dossier que le script `check_fb_bans.py`.

### ⚠️ Autoriser le compte de service sur le Google Sheet :
Copiez l'adresse e-mail de votre compte de service (celle qui termine par `@...iam.gserviceaccount.com`), ouvrez le document Google Sheet utilisé pour le suivi, cliquez sur **Partager** en haut à droite, et **ajoutez cette adresse email en tant qu'Éditeur**.

---

## ⚙️ 3. Paramétrage du script (Optionnel)

Ouvrez `check_fb_bans.py` avec un éditeur de texte. En haut du fichier, vous verrez une section `CONFIGURATION` :

```python
# ================= CONFIGURATION =================
CREDS_FILE = 'credentials.json'
SHEET_ID = '1QEpqh1fZhL0rhMvHfmH_6q5GFTQgJFxUH4ablG9c5Hs' # ID de votre Google Sheet
WORKSHEET_NAME = 'Suivi des proxys' # Nom exact de l'onglet
ADS_API = "http://127.0.0.1:50325/api/v1" # Port à vérifier dans AdsPower
THREADS = 4  # Nombre de fenêtres Chrome à ouvrir simultanément
TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID = "..."
# =================================================
```
- Vérifiez que le `SHEET_ID` correspond bien à l'ID de l'URL de votre document Google Sheet.
- **Vérifiez le port de l'API** (`50325`). Si dans les paramètres d'AdsPower le port est différent (ex: `50326`), modifiez la variable `ADS_API` en conséquence.
- Vous pouvez ajuster la variable `THREADS` selon la puissance de votre PC (4 est un bon compromis, mais vous pouvez le baisser à 2 ou 1 si le PC a du mal).

---

## 🚀 4. Lancement du Script (Automatisé)

1. **Assurez-vous qu'AdsPower est ouvert.**
2. Selon votre système d'exploitation, utilisez le script de lancement automatique (qui se chargera de créer l'environnement virtuel, d'installer les dépendances et de lancer le bot) :
   - **Sous Windows** : Double-cliquez sur le fichier `run_checker.bat` (ou lancez-le depuis un terminal).
   - **Sous Mac/Linux** : Lancez le script dans le terminal avec `./run_checker.sh` (assurez-vous qu'il soit exécutable avec `chmod +x run_checker.sh`).

Le script va automatiquement :
- Se connecter à AdsPower et récupérer les profils.
- Lire le Google Sheet.
- Lancer les navigateurs de manière invisible (ou via l'API) pour tester les comptes FB.
- Mettre à jour le Google Sheet.
- Vous envoyer le rapport final sur Telegram.

### En cas de problème de connexion API :
Si vous obtenez une erreur de connexion à AdsPower, retournez dans les Paramètres (Settings) de l'application AdsPower pour confirmer que l'API locale est bien activée, et vérifiez que le port indiqué correspond bien à celui dans le script (`ADS_API`). Vous pouvez utiliser le script `test_adspower.py` pour tester rapidement la connexion.

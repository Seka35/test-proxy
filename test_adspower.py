import requests
import json

# Remplace par l'URL exacte affichée dans tes paramètres API AdsPower
API_URL = "http://127.0.0.1:50325/api/v1/user/list"

def test_api():
    try:
        print("🔍 Test de connexion à l'API AdsPower...")
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                print("✅ Connexion réussie !\n")
                profiles = data.get("data", {}).get("list", [])
                print(f"📊 Nombre de profils trouvés (page 1) : {len(profiles)}\n")
                
                if profiles:
                    print("Voici les données brutes renvoyées par AdsPower pour le premier profil :")
                    print("-------------------------------------------------------------------")
                    print(json.dumps(profiles[0], indent=4, ensure_ascii=False))
                    print("-------------------------------------------------------------------")
                    print("\nCopie-colle ce résultat à ton assistant IA pour qu'il trouve les bons champs !")
            else:
                print(f"❌ Erreur de l'API : {data.get('msg')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Impossible de se connecter (AdsPower est-il bien ouvert ?) : {e}")

if __name__ == "__main__":
    test_api()

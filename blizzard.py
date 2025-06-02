import json
import requests
from urllib.parse import quote
import os

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ CLIENT_ID ou CLIENT_SECRET manquant !")
    sys.exit(1)
else:
    print(f"✅ CLIENT_ID and CLIENT_SECRET loaded (CLIENT_ID length: {len(CLIENT_ID)})")

def get_access_token():
    url = "https://eu.battle.net/oauth/token"
    response = requests.post(
        url,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_character_data(access_token, character_name):
    namespace = "profile-classic1x-eu"
    realm = "soulseeker"
    locale = "en_US"
    encoded_name = quote(character_name.lower())
    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{encoded_name}"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"namespace": namespace, "locale": locale}
    print(f"URL appelée : {url}?namespace={namespace}&locale={locale}")
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"❌ {character_name} : erreur 404 (peut-être niveau < 10 ou personnage inexistant)")
        return None
    else:
        print(f"❌ {character_name} : erreur {response.status_code}")
        return None

def get_character_talents(access_token, character_name):
    namespace = "profile-classic1x-eu"
    realm = "soulseeker"
    locale = "en_US"
    encoded_name = quote(character_name.lower())

    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{encoded_name}/talents"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"namespace": namespace, "locale": locale}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        # print(json.dumps(data, indent=2, ensure_ascii=False))  # debug si besoin
        return data
    elif response.status_code == 404:
        # Pas de talents si personnage < lvl10 ou autres cas
        print(f"⚠️ Talents non trouvés pour {character_name} (peut-être niveau < 10)")
        return None
    else:
        print(f"Erreur récupération talents {character_name}: {response.status_code}")
        return None

def determine_specialization_from_talents(talent_data):
    if not talent_data or "talents" not in talent_data:
        return None

    talents = talent_data["talents"]
    if not talents:
        return None

    # Trouver l'arbre avec le plus de points dépensés
    best_tree = max(talents, key=lambda t: t.get("spent_points", 0))
    return best_tree.get("talent_tree", {}).get("name")

def main():
    token = get_access_token()

    with open("liste.txt", "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    results = []

    for line in lines:
        # Split par virgule et strip
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            print(f"⚠️ Ligne mal formée ignorée : {line}")
            continue
        player_name, character_name = parts

        print(f"🔍 Récupération de {character_name} (pour {player_name})...")
        data = get_character_data(token, character_name)
        talent_data = get_character_talents(token, character_name)
        specialization = determine_specialization_from_talents(talent_data)

        if data:
            results.append({
                "player": player_name,                  # Le premier nom de la ligne
                "name": character_name,                 # Le second nom utilisé pour requête
                "level": data.get('level'),
                "class": data['character_class']['name'] if data.get('character_class') else None,
                "specialization": specialization,
                "race": data['race']['name'] if data.get('race') else None,
                "is_ghost": data.get('is_ghost', False),
                "average_item_level": data.get('average_item_level', None)
            })
            print(f"✅ {character_name} - Niveau {data['level']} | Classe : {data['character_class']['name']} | Race : {data['race']['name']} | Spé : {specialization}")
        else:
            results.append({
                "player": player_name,
                "name": character_name,
                "level": 0,
                "class": None,
                "race": None,
                "specialization": None,
                "is_ghost": None,
                "average_item_level": None
            })
        print()

    with open("resultats.json", "w", encoding="utf-8") as outfile:
        json.dump(results, outfile, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()

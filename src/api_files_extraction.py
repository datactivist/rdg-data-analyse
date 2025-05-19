import requests
import time
import os
import json
import pandas as pd

# Configuration
url_files = "https://entrepot.recherche.data.gouv.fr/api/v1/search?q=*&type=file&start={start}&per_page=100"
checkpoint_file = "checkpoint.txt"
json_filename = "files.json"
checkpoint_interval = 100

# Charger le dernier checkpoint
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r") as f:
        start = int(f.read().strip())
        print(f"Reprise à start={start} depuis le checkpoint.")
else:
    start = 0

per_page = 100
file_data = []

# Charger les données existantes si le fichier JSON existe
if os.path.exists(json_filename):
    with open(json_filename, "r", encoding="utf-8") as f:
        try:
            file_data = json.load(f)
            print(f"{len(file_data)} fichiers déjà chargés dans {json_filename}.")
        except json.JSONDecodeError:
            print("Erreur de lecture du fichier JSON existant. Création d'un nouveau fichier.")
            file_data = []

while True:
    url = url_files.format(start=start)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ChunkedEncodingError:
        print(f"Erreur de connexion à start={start}, tentative de reconnexion...")
        time.sleep(5)
        continue
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau : {e}")
        break

    data = response.json()
    items = data.get("data", {}).get("items", [])
    print(f"Start: {start} - Nombre d'items récupérés: {len(items)}")

    if not items:
        print("Aucun item retourné, fin de la pagination.")
        break

    # Afficher un exemple de structure JSON (pour analyse)
    if start == 0:
        print(json.dumps(items[:2], indent=4, ensure_ascii=False))

    # On récupères toutes les données des fichiers
    for item in items:
        file_entry = {
            "Nom du fichier": item.get("name", "Nom inconnu"),
            "ID du fichier": item.get("file_id", "ID inconnu"),
            "Type de fichier": item.get("file_type", "Type inconnu"),
            "Type MIME": item.get("file_content_type", "MIME inconnu"),
            "Taille (octets)": item.get("size_in_bytes", "Taille inconnue"),
            "Date de publication": item.get("published_at", "Date inconnue"),
            "Description": item.get("description", "Pas de description"),
            "MD5 Checksum": item.get("md5", "MD5 inconnu"),
            "ID persistant du fichier": item.get("file_persistent_id", "ID persistant inconnu"),
            "Nom du dataset": item.get("dataset_name", "Nom du dataset inconnu"),
            "ID du dataset": item.get("dataset_id", "ID du dataset inconnu"),
            "ID persistant du dataset": item.get("dataset_persistent_id", "ID persistant du dataset inconnu"),
            "Citation du dataset": item.get("dataset_citation", "Citation inconnue"),
            "URL de téléchargement": item.get("url", "URL inconnue"),
        }
        file_data.append(file_entry)

    # Sauvegarde périodique (checkpoint)
    if start % (per_page * checkpoint_interval) == 0:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=4, ensure_ascii=False)

        with open(checkpoint_file, "w") as f:
            f.write(str(start))

        print(f"Checkpoint sauvegardé à start={start}")

    if len(items) < per_page:
        break

    start += per_page

# Sauvegarde finale
with open(json_filename, "w", encoding="utf-8") as f:
    json.dump(file_data, f, indent=4, ensure_ascii=False)

with open(checkpoint_file, "w") as f:
    f.write(str(start))

print(f"Extraction terminée. {len(file_data)} fichiers extraits et sauvegardés dans {json_filename}.")


# Charger le fichier JSON
json_filename = "files.json"
excel_filename = "files.xlsx"

with open(json_filename, "r", encoding="utf-8") as f:
    file_data = json.load(f)

# Création du DataFrame pandas
df = pd.DataFrame(file_data)

# Sauvegarde au format Excel
df.to_excel(excel_filename, index=False, engine="openpyxl")

print(f"Conversion terminée ! Fichier Excel sauvegardé sous {excel_filename}.")

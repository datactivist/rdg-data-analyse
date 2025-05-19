import json
import csv
from pathlib import Path

corpus = Path("C:/Users/labo.adm/Documents/rdg/data/raw/rdg_corpus.json")

# Charger le fichier JSON
with open(corpus, "r", encoding="utf-8") as f:
    data = json.load(f)

# Trier les éléments par type
sorted_data = {"dataverse": [], "dataset": [], "file": []}

for item in data:
    item_type = item.get("type", "").lower()
    if item_type in sorted_data:
        sorted_data[item_type].append(item)

# Définition des colonnes CSV pour chaque type
dataverse_fields = ["type", "name", "identifier", "url", "description", "published_at"]
dataset_fields = [
    "type", "name", "global_id", "url", "description", "published_at",
    "publisher", "name_of_dataverse", "subjects", "fileCount", "majorVersion", "minorVersion",
    "createdAt", "updatedAt", "authors"
]
file_fields = [
    "type", "name", "file_id", "url", "description", "published_at",
    "file_type", "size_in_bytes", "md5", "dataset_name", "dataset_id"
]

# Fonction pour obtenir une valeur sans erreurs, en mettant "" si vide
def safe_get(item, key):
    value = item.get(key, "")
    if isinstance(value, list):  # Convertir les listes en texte
        return ", ".join(value) if value else ""
    return value

# Fonction pour écrire les fichiers CSV
def write_csv(filename, data, fields):
    with open(Path(f"rdg/data/{filename}"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in data:
            writer.writerow({field: safe_get(item, field) for field in fields})

# Générer les trois fichiers CSV séparés
write_csv("dataverse_from_corpus.csv", sorted_data["dataverse"], dataverse_fields)
write_csv("dataset_from_corpus.csv", sorted_data["dataset"], dataset_fields)
write_csv("file_from_corpus.csv", sorted_data["file"], file_fields)

print("Fichiers CSV générés avec succès !")

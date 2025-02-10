import csv
import json
from pathlib import Path


csv_file = Path("data/interim/dataverse_type.csv")
output_json_file = Path("data/interim/rdg_corpus_extended.json")


dataverse_by_type = {}

with open(csv_file, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        dataverse_type = row["type"]
        identifier = row["identifier"]
        if dataverse_type not in dataverse_by_type:
            dataverse_by_type[dataverse_type] = []  
        dataverse_by_type[dataverse_type].append(identifier)


with open(output_json_file, "w", encoding="utf-8") as file:
    json.dump(dataverse_by_type, file, indent=4, ensure_ascii=False)

print(f"Fichier JSON créé avec succès : {output_json_file}")

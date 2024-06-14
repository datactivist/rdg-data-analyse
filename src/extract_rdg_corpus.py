import json
import requests
from pathlib import Path

output_data_path = Path("data/raw")
output_data_path.mkdir(parents=True, exist_ok=True)

output_file = output_data_path / Path("rdg_corpus.json")

if output_file.exists():
    print(
        "Le fichier existe déjà, supprimez le si vous souhaiter l'extraire à nouveau."
    )
    exit()

datasets = []
shift = 0

while True:

    if shift % 1000 == 0:
        print(f"Extracting {shift}th item")
        # save checkpoint
        with open(output_file, "w") as f:
            json.dump(datasets, f, indent=4)

    # request page from RDG API
    r = requests.get(
        f"https://entrepot.recherche.data.gouv.fr/api/v1/search?q=*&start={shift}&per_page=100"
    )
    output = r.json()

    # break the loop if no data is found (i.e no more items to request)
    if (
        "data" not in output
        or "items" not in output["data"]
        or not output["data"]["items"]
    ):
        break

    shift += 100

    for item in output["data"]["items"]:
        datasets.append(item)


with open(output_file, "w") as f:
    json.dump(datasets, f, indent=4)

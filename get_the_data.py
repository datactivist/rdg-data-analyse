import json
import requests  # Assurez-vous d'importer le module 'requests'

total_datasets = []
page = 0  # Assurez-vous de définir une valeur initiale pour la variable 'page'

while True:  # Changez 'data' à 'True' pour un contrôle continu
    r = requests.get(f"https://entrepot.recherche.data.gouv.fr/api/v1/search?q=*&start={page}&per_page=100")
    data_search = r.json()
    
    # Vérifiez si 'data' contient la clé 'data' et si la liste 'items' est non vide
    if 'data' in data_search and 'items' in data_search['data'] and data_search['data']['items']:
        for item in data_search['data']['items']:
            total_datasets.append(item)

        page += 100
    else:
        break  # Sortez de la boucle si la liste d'éléments est vide

with open("data_search.json", 'w') as f:
    json.dump(total_datasets, f)


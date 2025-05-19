import requests
import pandas as pd
from pathlib import Path

def fetch_openaire_data(search_query, output_filename="resultats_openaire.xlsx"):
    """
    Fonction pour récupérer des données de l'API OpenAIRE et les enregistrer dans un fichier Excel.

    Paramètres :
        - search_query (str) : Le mot-clé de recherche (ex: "alert", "risk").
        - output_filename (str) : Nom du fichier Excel de sortie (par défaut 'resultats_openaire.xlsx').
    """

    # URL et paramètres de requête
    url = "https://api.openaire.eu/graph/v1/researchProducts"
    params = {
        "search": search_query,
        "type": "dataset",
        "page": 1,
        "pageSize": 100,
        "sortBy": "relevance DESC"
    }
    headers = {"accept": "application/json"}

    # Requête API
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        if results:
            # Extraction des données pertinentes
            extracted_data = []
            for item in results:
                # Extraction de l'URL (si instances existent)
                instances = item.get("instances", [])
                url_value = instances[0].get("urls", ["N/A"])[0] if instances else "N/A"

                extracted_data.append({
                    "mainTitle": item.get("mainTitle", "N/A"),
                    "Publisher": item.get("publisher", "N/A"),  # Extraction du publisher
                    "publicationDate": item.get("publicationDate", "N/A"),
                    "id": item.get("id", "N/A"),
                    "URL": url_value  # Ajout de l'URL
                })

            # Création du DataFrame pandas
            df = pd.DataFrame(extracted_data)

            # Sauvegarde en fichier Excel dans rdg/data/extraction_api
            df.to_excel(Path("rdg/data/extraction_api{output_filename}"), index=False, engine="openpyxl")

            print(f"Les résultats pour '{search_query}' ont été enregistrés dans '{output_filename}'.")
        else:
            print(f"Aucun résultat trouvé pour '{search_query}'.")
    else:
        print(f"Échec de récupération des données ({response.status_code}) pour '{search_query}'.")



#fetch_openaire_data("alert", "resultats_alert_openaire.xlsx")
#fetch_openaire_data("risk", "resultats_risk_openaire.xlsx")
#fetch_openaire_data("risque", "resultats_risque_openaire.xlsx")
#fetch_openaire_data("alerte", "resultats_alerte_openaire.xlsx")



from bs4 import BeautifulSoup
import requests
from pathlib import Path
import csv
from collections import Counter


# URL du site à scraper
url_template = "https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&types=dataverses&sort=dateSort&order=desc&page={page}"

def extract_identifier_from_href(href):

    if "jsessionid" in href:
        href = href.split(";")[0]

    return href.split("/")[-1]

dataverse = []
dataverse_dict = {}
page = 1

while True:
    html_filename = Path(f"data/interim/dataverses/{page}.html")

    # Vérifier si le fichier HTML est en cache
    if html_filename.exists():
        print(f"Utilisation du cache HTML pour la page {page}")
        with open(html_filename, "r", encoding="utf-8") as file:
            html_text = file.read()
    else:
        print(f"Téléchargement de la page {page} depuis {url_template.format(page=page)}")
        response = requests.get(url_template.format(page=page))

        if response.status_code != 200:
            print(f"Échec du téléchargement de la page {page}")
            break  # Arrêter en cas d'échec de la requête

        html_text = response.text

        # Sauvegarde du fichier HTML en cache
        html_filename.parent.mkdir(parents=True, exist_ok=True)
        with open(html_filename, "w", encoding="utf-8") as file:
            file.write(html_text)

    # Analyse HTML avec BeautifulSoup
    html = BeautifulSoup(html_text, "html.parser")

    # Extraction des sous-collections
    sous_collections = html.find_all("div", class_="dataverseResult clearfix")
    
    for collection in sous_collections:
        span_with_title = collection.find('span', style='padding:4px 0;')
        titre_collection = span_with_title.text.strip() if span_with_title else "Titre inconnu"
        
        lien = collection.find('a', href=True)
        if lien and "/dataverse/" in lien['href']:
            dataverse_id = lien['href'].split("/dataverse/") [-1]
            identifier = extract_identifier_from_href(dataverse_id)  # Extraction de l'ID
        else:
            dataverse_id = f"ID_inconnu_Page_{page}"  # On ajoute la page pour éviter les écrasements

        # Ajout avec clé unique ID+Titre pour éviter les doublons
        #clef_unique = f"{identifier} - {titre_collection}"
        dataverse_dict[identifier] = {"Titre": titre_collection}

        dataverse.append(titre_collection)
    # Si moins de 10 résultats sur la page, arrêter
    if len(sous_collections) < 10:
        break

    page += 1

# Enregistrement des données dans un fichier CSV
dataverse_file = Path("data/interim/dataverses.csv")

with open(dataverse_file, "w", encoding="utf-8", newline="") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["identifier", "Nom du Dataverse"])  # En-tête CSV
    for  identifier , titre in dataverse_dict.items():
        writer.writerow([identifier , titre ])





# Compter les occurrences
compteur = Counter(dataverse)

# Afficher les doublons
doublons = {elem: count for elem, count in compteur.items() if count > 1}
print("Doublons trouvés :", doublons , len(doublons))

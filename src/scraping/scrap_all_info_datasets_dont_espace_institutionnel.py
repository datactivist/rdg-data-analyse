from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from pathlib import Path
import re

# Dossier de cache
CACHE_DIR = Path("data/interim/datasets")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def extract_identifier_from_href(href):
    """Extrait uniquement la fin du DOI (ex: ZZGICL) à partir de l'URL."""
    match = re.search(r"doi:10\.\d{5}/([\w\d]+)", href)
    return match.group(1) if match else "ID_inconnu"

datasets_info = []
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

page = 1
while True:
    html_filename = CACHE_DIR / f"page{page}.html"

    # Vérifier si la page est déjà téléchargée
    if html_filename.exists():
        print(f"Utilisation du cache pour la page {page}")
        with open(html_filename, "r", encoding="utf-8") as file:
            html_text = file.read()
    else:
        print(f"Téléchargement de la page {page}")
        link = f"https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&types=datasets&sort=dateSort&order=desc&page={page}"
        try:
            response = session.get(link, timeout=10)
            response.raise_for_status()
            html_text = response.text
            # Sauvegarder la page téléchargée
            with open(html_filename, "w", encoding="utf-8") as file:
                file.write(html_text)
        except requests.RequestException as e:
            print(f"Échec du téléchargement de la page {page} : {e}")
            break

    html = BeautifulSoup(html_text, "html.parser")
    jeu_de_donnees = html.find_all("div", class_="datasetResult clearfix")

    # Vérifier s'il y a encore des datasets
    if not jeu_de_donnees:
        print("Fin de pagination : plus de datasets disponibles.")
        break

    for jeu in jeu_de_donnees:
        titre_element = jeu.find("a", href=True)
        titre_jeu = titre_element.text.strip() if titre_element else "Titre inconnu"
        dataset_url = f"https://entrepot.recherche.data.gouv.fr{titre_element['href']}" if titre_element else None
        identifier = extract_identifier_from_href(titre_element['href']) if dataset_url else f"ID_inconnu_Page_{page}"

        html_filename_datasets = CACHE_DIR / f"{identifier}.html"

        # Vérifier si le dataset est déjà téléchargé
        if html_filename_datasets.exists():
            print(f"Utilisation du cache pour le dataset {titre_jeu}")
            with open(html_filename_datasets, "r", encoding="utf-8") as f:
                html_text_dataset = f.read()
        else:
            print(f"Téléchargement du dataset {titre_jeu}")
            try:
                rep_dataset_id = session.get(dataset_url, timeout=10)
                rep_dataset_id.raise_for_status()
                html_text_dataset = rep_dataset_id.text
                # Sauvegarder le dataset téléchargé
                with open(html_filename_datasets, "w", encoding="utf-8") as f:
                    f.write(html_text_dataset)
            except requests.RequestException as e:
                print(f"Échec du téléchargement du dataset {identifier} : {e}")
                continue

        html_dataset = BeautifulSoup(html_text_dataset, "html.parser")

        # Extraction des métadonnées
        def extract_text(tag_id):
            tag = html_dataset.find("tr", id=tag_id)
            return tag.find("td").text.strip() if tag and tag.find("td") else "N/A"

        title = extract_text("metadata_title")
        publication_date = extract_text("metadata_publicationDate")
        description = extract_text("dsDescription")
        keywords = extract_text("keywords")
        thematique = extract_text("metadata_topicClassification")
        origine = extract_text("metadata_dataOrigin")

        lien_espace = html_dataset.find("a", id="breadcrumbLnk1")
        espace = lien_espace["href"].split("/dataverse/")[-1] if lien_espace else "Espace inconnu"

        datasets_info.append([dataset_url, title, espace, publication_date, description, thematique, origine, keywords])

    page += 1  # Passage à la page suivante

# Sauvegarde des données dans un fichier Excel
columns = ["URL", "Titre", "Espace Institutionnel", "Date de publication", "Description", "Thématique", "Origine", "Mots-clés"]
df_final = pd.DataFrame(datasets_info, columns=columns)
df_final.to_excel("extracted_data.xlsx", engine="openpyxl", index=False)

print("Les données ont été extraites et exportées vers 'extracted_data.xlsx'.")

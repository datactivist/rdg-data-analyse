from bs4 import BeautifulSoup
import requests
from pathlib import Path
import csv
import re

url_template = "https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&types=datasets&sort=dateSort&order=desc&page={page}"

def extract_identifier_from_href(href):
    if "jsessionid" in href:
        href = href.split(";")[0]
    return href.split("/")[-1]

def get_metadata_from_keywords(soup, row_id):
    row = soup.find("tr", id=row_id)
    text = row.find("td").decode_contents() if row and row.find("td") else "Non renseigné"
    keywords = re.split(r'<br\s*/?>', text)
    output = []

    for keyword in keywords:
        keyword_soup = BeautifulSoup(keyword, "html.parser")
        for span in keyword_soup.find_all("span"):
            span.replace_with(span.text + ";")
        keyword_text = keyword_soup.text
        keyword_text = re.sub(r'(\s+)(https?://)', r'; \2', keyword_text)
        output.append(keyword_text.strip())

    return output

def dataset_extractor(link_template, nom_fichier):
    dataset_dict = {}
    page = 1

    while True:
        html_filename = Path(f"data/interim/datasets/{nom_fichier}_{page}.html")

        if html_filename.exists():
            print(f"Utilisation du cache HTML pour la page {page}")
            with open(html_filename, "r", encoding="utf-8") as file:
                html_text = file.read()
        else:
            print(f"Téléchargement de la page {page}")
            response = requests.get(link_template.format(page=page))

            if response.status_code != 200:
                print(f"Échec du téléchargement de la page {page}")
                break  

            html_text = response.text
            html_filename.parent.mkdir(parents=True, exist_ok=True)
            with open(html_filename, "w", encoding="utf-8") as file:
                file.write(html_text)

        html = BeautifulSoup(html_text, "html.parser")
        jeu_de_donnees = html.find_all("div", class_="datasetResult clearfix")

        for jeu in jeu_de_donnees:
            span_with_title = jeu.find('span', style='padding:4px 0;')
            titre_jeu = span_with_title.text.strip() if span_with_title else "Titre inconnu"

            lien = jeu.find('a', href=True)
            if lien and "/dataset" in lien['href']:
                dataset_id = lien['href']
                identifier = extract_identifier_from_href(dataset_id)
            else:
                identifier = f"ID_inconnu_Page_{page}"

            dataset_doi = dataset_id.split("doi:")[1]
            dataset_url = f"https://doi.org/{dataset_doi}"

            html_filename_datasets = Path(f"data/interim/datasets/{nom_fichier}_{identifier}.html")

            if html_filename_datasets.exists():
                print(f"Utilisation du cache pour le dataset {titre_jeu}")
                with open(html_filename_datasets, "r", encoding="utf-8") as f:
                    html_text_dataset = f.read()
            else:
                print(f"Téléchargement du dataset {titre_jeu}")
                rep_dataset_url = requests.get(dataset_url, allow_redirects=True)

                if rep_dataset_url.status_code == 200:
                    html_text_dataset = rep_dataset_url.text
                else:
                    print(f"Erreur {rep_dataset_url.status_code} pour {dataset_url}")
                    continue  

                html_filename_datasets.parent.mkdir(parents=True, exist_ok=True)
                with open(html_filename_datasets, "w", encoding="utf-8") as f:
                    f.write(html_text_dataset)

            html_datasets = BeautifulSoup(html_text_dataset, "html.parser")
            lien_espace = html_datasets.find("a", id="breadcrumbLnk1")
            espace = lien_espace["href"].split("/dataverse/")[-1] if lien_espace else "Espace inconnu"

            site = html_datasets.find("body").get("data-sitename") if html_datasets.find("body") else None


            if site == "dat@UBFC":
                keywords_section = html_datasets.find("strong", class_="genMetasAlign", string=lambda text: text and "Keywords" in text)

                if keywords_section:
                    keywords_div = keywords_section.find_next("div", class_="multilineValue")

                    if keywords_div:
                        mot_clefs = [a.text.strip() for a in keywords_div.find_all("a")]
                        print(f"Mots-clés extraits pour {titre_jeu} :", mot_clefs)
                    else:
                        mot_clefs = ["Mots-clés non trouvés"]
                else:
                    mot_clefs = ["Section Keywords non trouvée"]


            else:
                mot_clefs = get_metadata_from_keywords(html_datasets, "metadata_keyword")

            dataset_dict[dataset_id] = {"Titre": titre_jeu, "Espace institutionnel": espace, "Mots-clefs": mot_clefs}

        if len(jeu_de_donnees) < 10:
            break

        if page % 10 == 0:
            print(f"Sauvegarde des données après {page} pages...")
            dataset_file_keywords = Path("data/datasets_keywords.csv")
            with open(dataset_file_keywords, "w", encoding="utf-8", newline="") as output_file:
                writer = csv.writer(output_file, delimiter=";")
                writer.writerow(["doi", "Nom du dataset", "Espace institutionnel", "Mots-clefs"])
                for dataset_id, data in dataset_dict.items():
                    for mot_clef in data["Mots-clefs"]:
                        writer.writerow([dataset_id, data["Titre"], data["Espace institutionnel"], mot_clef])

        page += 1

    dataset_file_keywords = Path("data/datasets_keywords.csv")
    with open(dataset_file_keywords, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, delimiter=";")
        writer.writerow(["doi", "Nom du dataset", "Espace institutionnel", "Mots-clefs"])
        for dataset_id, data in dataset_dict.items():
            for mot_clef in data["Mots-clefs"]:
                writer.writerow([dataset_id, data["Titre"], data["Espace institutionnel"], mot_clef])

dataset_extractor(url_template, "")

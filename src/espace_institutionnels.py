from bs4 import BeautifulSoup
import requests
from pathlib import Path
import pandas as pd
import re
import csv


html_dir = Path("data/interim/espaces")
html_dir.mkdir(parents=True, exist_ok=True)  # Crée le répertoire si nécessaire


def extract_identifier_from_href(href):
    if "jsessionid" in href:
        href = href.split(";")[0]
    return href.split("/")[-1]


base_url = "https://recherche.data.gouv.fr/fr/etablissements"


page_num = 1


all_data = []
all_identifiers = []


while True:

    html_filename = html_dir / f"espaces_{page_num}.html"

    if html_filename.exists():
        print("Used cached HTML")
        with open(html_filename, "r", encoding="utf-8") as file:
            html_text = file.read()
            html = BeautifulSoup(html_text, "html.parser")
    else:
        url = f"{base_url}?page={page_num}"
        response = requests.get(url)

        if response.status_code == 200:
            print("Page récupérée avec succès!")
            html_text = response.text

            with open(html_filename, "w", encoding="utf-8") as file:
                file.write(html_text)

    html = BeautifulSoup(html_text, "html.parser")

    blocs_institutionnels = html.find_all("section", class_="fr-accordion")
    print(f"Nombre de blocs trouvés : {len(blocs_institutionnels)}")

    for bloc in blocs_institutionnels:
        # Noms
        bouton = bloc.find("button", class_="fr-accordion__btn")
        nom_institution = bouton.text.strip() if bouton else "Nom inconnu"

        # Liens
        liens_group = bloc.find("ul", class_="fr-tags-group")
        liens = []
        if liens_group:
            for lien in liens_group.find_all("a"):
                if "dataverse" in lien["href"]:
                    liens.append(lien["href"])
                    entry = {
                        "Espace institutionnel": nom_institution,
                        "Lien vers l'espace": lien["href"],
                        "Nombre de sous-collections": 0,
                        "Nombre de jeux de données": 0,
                        "Sous-collections": [],  # Initialisation correcte de la clé
                        "identifier": [],
                    }
                    all_data.append(entry)

    if len(blocs_institutionnels) < 20:
        break

    page_num += 1


# Accéder aux espaces pour récupérer leurs collections


def extraire_nbr_collections(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    span = soup.find("span", class_="facetTypeDataverse")

    if span:
        match = re.search(r"Dataverses \((\d+)\)", span.text)
        if match:
            return int(match.group(1))  # Retourner le nombre extrait
    return 0  # Retourner 0 si aucune correspondance n'est trouvée


def extraire_nbr_datasets(html_content):
    """Extrait le nombre de jeux de données en prenant en charge les séparateurs de milliers."""
    soup = BeautifulSoup(html_content, "html.parser")
    span = soup.find("span", class_="facetTypeDataset")

    if span and span.text.strip():
        match = re.search(
            r"Datasets \(([\d,.]+)\)", span.text.strip()
        )  # Capture 3,106 ou 2.500
        if match:
            nombre_jdd = (
                match.group(1).replace(",", "").replace(".", "")
            )  # Supprime les séparateurs
            return int(nombre_jdd)  # Convertit en entier

    return 0


for entry in all_data:
    lien = entry["Lien vers l'espace"]
    num_page = 1
    entry["Nombre de sous-collections "] = 0
    nombre_jdd_extrait = False
    total_collections = 0
    list_identifier = []

    while True:
        lien_complet = (
            f"{lien}&page={num_page}" if "?" in lien else f"{lien}?page={num_page}"
        )
        html_filename = (
            html_dir
            / f"{entry['Espace institutionnel'].replace(' ', '_')}_{num_page}.html"
        )
        if html_filename.exists():
            print("cache used for", html_filename)
            with open(html_filename, "r", encoding="utf-8") as file:
                html_text = file.read()
        else:
            rep = requests.get(lien_complet)
            if rep.status_code != 200:
                print(
                    f"Erreur lors de la récupération de la page {num_page} pour {lien}"
                )
                print(rep.status_code, rep.url)
                break

            html_text = rep.text

            with open(html_filename, "w", encoding="utf-8") as file:
                file.write(html_text)

        if not nombre_jdd_extrait:
            entry["Nombre de jeux de données"] = extraire_nbr_datasets(html_text)
            print(
                f"{entry['Espace institutionnel']} - {entry['Nombre de jeux de données']} jeux de données"
            )
            nombre_jdd_extrait = True  # On ne met plus à jour après la première page

        nbr_collections = extraire_nbr_collections(html_text)
        if nbr_collections == 0:
            print(f"0 collection pour {lien_complet}")
            break

        dataverse_html = BeautifulSoup(html_text, "html.parser")
        # Trouver les sous-collections
        sous_collections = dataverse_html.find_all(
            "div", class_="dataverseResult clearfix"
        )

        for collection in sous_collections:
            span_with_title = collection.find("span", style="padding:4px 0;")
            titre_collection = (
                span_with_title.text.strip() if span_with_title else "Titre inconnu"
            )
            if titre_collection not in entry["Sous-collections"]:
                entry["Sous-collections"].append(titre_collection)
            else:
                entry["Sous-collections"].append("{titre_collection}{num_page}")

            lien_sous_collection = (
                collection.find("a")["href"] if collection.find("a") else ""
            )
            if lien_sous_collection:
                sub_identifier = extract_identifier_from_href(lien_sous_collection)
                list_identifier.append(sub_identifier)
                all_identifiers.append(
                    {
                        "identifier": sub_identifier,  # Identifiant de la sous-collection
                        "Espace institutionnel": entry["Espace institutionnel"],
                    }
                )

        total_collections += len(sous_collections)
        entry["Nombre de sous-collections "] = total_collections

        if total_collections >= nbr_collections:
            break  # toutes les sous-collections sont récupérées

        num_page += 1

data_dict = {}


for entry in all_data:
    espace = entry["Espace institutionnel"]
    nombre_collections = len(entry["Sous-collections"])
    sous_collections = ", ".join(
        entry["Sous-collections"]
    )  # Transformer la liste en une chaîne
    nbr_jdds = entry["Nombre de jeux de données"]

    data_dict[espace] = nombre_collections, nbr_jdds, sous_collections, list_identifier


df_id = pd.DataFrame(all_identifiers)
df = pd.DataFrame(
    [(key, value[0], value[1], value[2]) for key, value in data_dict.items()],
    columns=[
        "Espace institutionnel",
        "Nombre de sous-collections",
        "Nombre de jeux de données",
        "Sous-collections",
    ],
)


with pd.ExcelWriter(
    "espaces_institutionnels_collections.xlsx", engine="openpyxl"
) as writer:
    df.to_excel(writer, sheet_name="Toutes les collections", index=False)


expanded_data = []
for entry in all_data:
    espace = entry["Espace institutionnel"]
    for sous_collection in entry["Sous-collections"]:
        expanded_data.append(
            {"Espace institutionnel": espace, "Sous-collection": sous_collection}
        )


df_expanded = pd.DataFrame(expanded_data)


output_excel_file_2 = "espaces_institutionnels_collections_par_feuille.xlsx"

output_excel_file_2 = "espaces_institutionnels_collections_par_feuille.xlsx"
with pd.ExcelWriter(output_excel_file_2, engine="openpyxl") as writer:
    for espace, group in df_expanded.groupby("Espace institutionnel"):
        sheet_name = espace[:31]  # Excel limite les noms d'onglets à 31 caractères
        group[["Sous-collection"]].to_excel(
            writer, sheet_name=sheet_name, index=False
        )  # Supprimer la colonne inutile


output_csv_file = Path("data/interim/espaces_institutionnels_identifiers.csv")
with open(output_csv_file, "w", encoding="utf-8", newline="") as file:
    fieldnames = ["identifier", "Espace institutionnel"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_identifiers)

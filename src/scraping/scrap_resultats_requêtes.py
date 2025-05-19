from bs4 import BeautifulSoup
import requests
import pandas as pd
from pathlib import Path
import os
import time

# Liens de recherche
alerte = "https://entrepot.recherche.data.gouv.fr/dataverse/root/?q=alerte"
alert = "https://entrepot.recherche.data.gouv.fr/dataverse/root/?q=alert"
risque = "https://entrepot.recherche.data.gouv.fr/dataverse/root/?q=risque"
risk = "https://entrepot.recherche.data.gouv.fr/dataverse/root/?q=risk"

# Dossier de cache
CACHE_DIR = Path("data/interim/keywords")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def extraire_fin_lien(lien):
    """Extrait la partie après le dernier slash dans un lien."""
    return os.path.basename(lien.split("?q=")[-1])

def sauvegarder_page(html_text, filename):
    """Sauvegarde une page HTML localement."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_text)

def charger_page_cache(filename):
    """Charge une page HTML depuis le cache si elle existe."""
    if filename.exists():
        print(f"Utilisation du cache pour {filename}")
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    return None

def data_extraction(link, nom_fichier): 
    """Extrait les données de recherche et stocke les résultats dans un fichier Excel."""
    data = []
    page = 1

    while True:
        # Définir le fichier cache pour cette page
        safe_link = extraire_fin_lien(link)
        filename = CACHE_DIR / f"{safe_link}_page_{page}.html"

        html_text = charger_page_cache(filename)
        if html_text is None:
            response = requests.get(link + f"&page={page}")
            if response.status_code != 200:
                print(f"Erreur lors de la récupération de la page {page} pour {link}")
                break  
            html_text = response.text
            sauvegarder_page(html_text, filename)
            time.sleep(2)  # Pause pour éviter de surcharger le serveur

        html = BeautifulSoup(html_text, "html.parser")
        table = html.find("table", {"id": "resultsTable"})
        if not table: 
            print("Pas trouvé table, arrêt de l'extraction.")
            break

        dataset_divs = table.find_all("td")
        for td in dataset_divs:
            type_categorie = "Inconnu"
            if td.find("div", class_="dataverseResult clearfix"):
                type_categorie = "Dataverse"
            elif td.find("div", class_="datasetResult clearfix"):
                type_categorie = "Dataset"
            elif td.find("div", class_="fileResult clearfix"):
                type_categorie = "File"

            titre_tag = td.find("a")
            titre = titre_tag.text.strip() if titre_tag else "Non renseigné"
            lien = "https://entrepot.recherche.data.gouv.fr" + titre_tag["href"] if titre_tag else "Non renseigné"

            rep = requests.get(lien)
            if rep.status_code != 200:
                print(f"Erreur lors de la récupération de la page pour {lien}")
                continue

            soup_detail = BeautifulSoup(rep.text, "html.parser")

            def get_text_from_row(soup, row_id):
                row = soup.find("tr", id=row_id)
                return row.find("td").get_text(strip=True) if row and row.find("td") else f"Non renseigné pour {titre}"

            if type_categorie == "Dataset":
                description = get_text_from_row(soup_detail, "metadata_dsDescription")
                sujet = get_text_from_row(soup_detail, "metadata_subject")
                thematique = get_text_from_row(soup_detail, "metadata_topicClassification")
                mot_clef = get_text_from_row(soup_detail, "metadata_keyword")
            elif type_categorie == "Dataverse":
                description_div = soup_detail.find("div", {"id": "dataverseDesc"})  
                description = description_div.get_text(strip=True) if description_div else f"Description non trouvée pour {titre}"
                sujet, thematique, mot_clef = f"Pas de sujet pour {titre}", f"Pas de thématique pour {titre}", f"Pas de mot-clefs pour {titre}"
            elif type_categorie == "File":
                description = get_text_from_row(soup_detail, "fileDescriptionBlock")
                breadcrumbs = soup_detail.find_all("a", id=lambda x: x and x.startswith("breadcrumbLnk"))
                if breadcrumbs:
                    dernier = breadcrumbs[-1]  
                    texte = dernier.get_text(strip=True)
                sujet = texte
                thematique = f"Pas de thématique pour {titre}"
                mot_clef = f"Pas de mots-clés pour {titre}"

            data.append({
                "Type": type_categorie,
                "Titre": titre,
                "Lien": lien,
                "Description": description,
                "Sujet": sujet,
                "Thématique": thematique,
                "Mots-clés": mot_clef
            })

        if len(dataset_divs) < 10:
            print(f"Fin de la pagination : {len(dataset_divs)} résultats trouvés sur la page {page}.")
            break
        page += 1  

    df = pd.DataFrame(data)
    df.to_excel(Path(f"rdg/data/extraction_resultats_{nom_fichier}.xlsx"), sheet_name="Résultats", index=False)
    print(f"Extraction terminée et fichier Excel généré sous le nom : extraction_resultats_{nom_fichier}.xlsx")

# Appel de la fonction
data_extraction(alerte, "alerte")
data_extraction(alert , "alert")
data_extraction(risque , "risque")
data_extraction(risk , "risk")

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from pathlib import Path
import csv
import re
import os

# Configuration de session avec retries
session = requests.Session()
retries = Retry(
    total=5,  
    backoff_factor=1,  
    status_forcelist=[500, 502, 503, 504],  
)
session.mount("https://", HTTPAdapter(max_retries=retries))

url_template = "https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&types=datasets&sort=dateSort&order=desc&page={page}"

# Liste de mots-clés pour filtrer les fichiers
mots_cles = {"readme", "README", "Readme", "read_me", "read-me", "READ_ME", "READ-ME", "LISEZ_MOI", "lisez_moi", "lisez-moi", "LISEZ-MOI" , "Lisez-moi" , "Lisezmoi" , "LISEZMOI" , "lisezmoi" , "Lisez_moi"}

def extract_filename_from_href(href):
    # Extrait l'identifiant complet du DOI
    match = re.search(r"(doi:10\.\d{5}/.+)", href)
    if match:
        identifier = match.group(1)
        # Remplace les caractères interdits par un underscore
        filename = re.sub(r'[\/:*?"<>|]', '_', identifier)
        return filename

def dataset_extractor(link_template, nom_fichier):
    dataset_dict = {}  
    filtered_dataset_dict = {}  
    page = 1
    page_size = 10  # Nombre d'éléments par page
    total_files = 0  # Exemple de nombre total de fichiers (à extraire du HTML)
    files_per_page = 10 


    while True:
        html_filename = Path(f"data/interim/datasets/{nom_fichier}_{page}.html")

        if html_filename.exists():
            print(f"Utilisation du cache HTML pour la page {page}")
            with open(html_filename, "r", encoding="utf-8") as file:
                html_text = file.read()
        else:
            print(f"Téléchargement de la page {page}")
            try:
                response = session.get(link_template.format(page=page), timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Échec du téléchargement de la page {page} : {e}")
                break

            html_text = response.text
            html_filename.parent.mkdir(parents=True, exist_ok=True)
            with open(html_filename, "w", encoding="utf-8") as file:
                file.write(html_text)

        html = BeautifulSoup(html_text, "html.parser")
        jeu_de_donnees = html.find_all("div", class_="datasetResult clearfix")

        for jeu in jeu_de_donnees:
            titre_element = jeu.find("a", href=True)
            titre_jeu = titre_element.text.strip() if titre_element else "Titre inconnu"

            # Construction du bon lien en fonction de l'institution
            if titre_element:
                href = titre_element['href']

                # Chercher l'entrepôt d'origine (CIRAD ou autre)
                entrepot_element = jeu.find("div", class_="text-muted small margin-top-half")
                dataset_url = None  # Valeur par défaut

                if entrepot_element:
                    texte_entrepot = entrepot_element.text.strip()

                    # Chercher tous les liens dans le texte de la balise
                    liens = re.findall(r"https?://[^\s)]+", texte_entrepot)

                    if not dataset_url and liens:
                        dataset_url = "".join(liens) + href  
                        print("entrepot détecté :" , dataset_url)

                    elif not dataset_url and not liens : 
                        span_balise = jeu.find("span", class_="text-muted", string=" - ")
                        entrepot_lien = span_balise.find_next("a")

                        if entrepot_lien:
                            entrepot_nom = entrepot_lien.get_text(strip=True)  # Récupère le texte du lien
                            entrepot_url = entrepot_lien["href"]  # Récupère l'URL de l'entrepôt

                        # Si l'URL est relative, compléter avec le domaine de base
                            if entrepot_url.startswith("/"):
                                entrepot_url = f"https://entrepot.recherche.data.gouv.fr{entrepot_url}"
                            dataset_url = entrepot_url
                            print(f"Entrepôt trouvé: {entrepot_nom} ({entrepot_url})")
                        
                # Si aucune URL spécifique n'a été trouvée, utiliser l'URL classique
                if not dataset_url:
                    dataset_url = f"https://entrepot.recherche.data.gouv.fr{href}"

            if dataset_url:
                identifier = extract_filename_from_href(titre_element['href'])
            else:
                identifier = f"ID_inconnu_Page_{page}"

            html_filename_datasets = Path(f"data/interim/datasets/{nom_fichier}_{identifier}.html")

            if html_filename_datasets.exists():
                print(f"Utilisation du cache pour le dataset {identifier}")
                with open(html_filename_datasets, "r", encoding="utf-8") as f:
                    html_text_dataset = f.read()
            else:
                print(f"Téléchargement du dataset {titre_jeu}")
                try:
                    rep_dataset_id = session.get(dataset_url, timeout=10)
                    rep_dataset_id.raise_for_status()
                except requests.RequestException as e:
                    print(f"Échec du téléchargement du dataset {identifier} : {e}")
                    continue

                html_text_dataset = rep_dataset_id.text
                html_filename_datasets.parent.mkdir(parents=True, exist_ok=True)
                with open(html_filename_datasets, "w", encoding="utf-8") as f:
                    f.write(html_text_dataset)

            # Analyser immédiatement le HTML pour éviter les décalages
            html_datasets = BeautifulSoup(html_text_dataset, "html.parser")

            lien_espace = html_datasets.find("a", id="breadcrumbLnk1")
            espace = lien_espace["href"].split("/dataverse/")[-1] if lien_espace else "Espace inconnu"

            origine_tag = html_datasets.find("tr", id="metadata_dataOrigin")
            origine = origine_tag.find("td").text.strip() if origine_tag and origine_tag.find("td") else "Pas d'origine renseignée"
            
            noms_fichiers = []
            if not noms_fichiers:
                fichiers = html_datasets.find_all("div", class_="fileNameOriginal")
                noms_fichiers = [f.text.strip() for f in fichiers] if fichiers else []

                # Gestion de la pagination pour les fichiers 

            #elif not noms_fichiers:  # Si la première méthode n'a rien trouvé
            #   dl_btns = html_datasets.find_all("a", class_="dlBtn")
            #   noms_fichiers = [btn.text.strip() for btn in dl_btns] if dl_btns else []

                if not noms_fichiers:  # Si toujours rien trouvé
                    noms_fichiers = ["pas de fichier"]

            # Vérification des fichiers avant de les ajouter
            dataset_dict[dataset_url] = {
                "Titre": titre_jeu,
                "Espace institutionnel": espace,
                "Fichiers": ", ".join(noms_fichiers),
                "Origine": origine
            }

            # Vérification si au moins un fichier contient un mot-clé
            fichiers_correspondants = []
            for f in noms_fichiers:
                f = f.strip()
                for mot in mots_cles:
                    if mot in f: 
                        fichiers_correspondants.append(f)
                         
            print(fichiers_correspondants)

            if fichiers_correspondants:  # Vérifie s'il y a au moins un fichier README trouvé
                filtered_dataset_dict[dataset_url] = {
                    "Titre": titre_jeu,
                    "Espace institutionnel": espace,
                    "Fichiers": ", ".join(fichiers_correspondants),
                    "Origine": origine
                }

        if len(jeu_de_donnees) < 10:
            break

        page += 1

    # Sauvegarde du fichier complet
    dataset_file = Path("data/interim/datasets.csv")
    with open(dataset_file, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, delimiter=";")
        writer.writerow(["URL du dataset", "Nom du dataset", "Espace institutionnel", "Fichiers", "Origine"])
        for dataset_url, data in dataset_dict.items():
            writer.writerow([dataset_url, data["Titre"], data["Espace institutionnel"], data["Fichiers"], data["Origine"]])


    print(f"Nombre de datasets filtrés : {len(filtered_dataset_dict)}")
    if not filtered_dataset_dict:
        print(" Aucun dataset filtré n'a été ajouté. Vérifiez les mots-clés et les noms de fichiers.")

    # Sauvegarde du fichier filtré
    filtered_dataset_file = Path("data/interim/datasets_filtered.csv")
    with open(filtered_dataset_file, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, delimiter=";")
        writer.writerow(["URL du dataset", "Nom du dataset", "Espace institutionnel", "Fichiers"])
        for dataset_url, data in filtered_dataset_dict.items():
            writer.writerow([dataset_url, data["Titre"], data["Espace institutionnel"], data["Fichiers"]])


dataset_extractor(url_template, "")

df = pd.read_excel("data/interim/moissonubfc.xlsx")

def extractor_UBFC(file) :

# Charger le fichier Excel contenant les URLs
    df = pd.read_excel(file)

    # Vérifier que la colonne contenant les URLs existe
    if "url" not in df.columns:
        raise ValueError("La colonne 'url' est absente du fichier Excel.")

    # Créer un dossier pour stocker les fichiers HTML
    dossier_html = "data/interim/html_pages"
    os.makedirs(dossier_html, exist_ok=True)

    # Dictionnaire pour stocker les résultats
    resultats = {}

    for index, row in df.iterrows():
        url = row["url"]  # Récupérer l'URL de la colonne 'url'
        nom_fichier_html = os.path.join(dossier_html, f"page_{index}.html")

        # Vérifier si la page HTML est déjà téléchargée
        if os.path.exists(nom_fichier_html):
            print(f"Chargement local : {nom_fichier_html}")
            with open(nom_fichier_html, "r", encoding="utf-8") as f:
                html_text = f.read()
        else:
            try:
                print(f"Téléchargement : {url}")
                rep = requests.get(url, timeout=5)
                rep.raise_for_status()  # Vérifie si la requête a réussi
                html_text = rep.text

                # Sauvegarder la page HTML localement
                with open(nom_fichier_html, "w", encoding="utf-8") as f:
                    f.write(html_text)
            except requests.RequestException as e:
                print(f"Erreur lors de l'accès à {url}: {e}")
                resultats[url] = "Erreur d'accès"
                continue  # Passer à l'URL suivante

        # Analyser la page HTML avec BeautifulSoup
        html = BeautifulSoup(html_text, "html.parser")
        dl_btns = html.find_all("a", class_="dlBtn")
        noms_fichiers = [btn.text.strip() for btn in dl_btns] if dl_btns else ["Aucun fichier trouvé"]

        # Ajouter les fichiers dans un format CSV friendly
        resultats[url] = ", ".join(noms_fichiers)

    # Convertir en DataFrame et enregistrer dans un fichier CSV avec `;` comme séparateur
    df_resultats = pd.DataFrame(list(resultats.items()), columns=["URL", "Fichiers"])
    df_resultats.to_csv("data/interim/resultats.csv", index=False, encoding="utf-8", sep=";")

    
#extractor_UBFC("data/interim/moissonubfc.xlsx")
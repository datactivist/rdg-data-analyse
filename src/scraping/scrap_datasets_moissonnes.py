from bs4 import BeautifulSoup
import requests
from pathlib import Path
import csv
import re

page = 1
url_template = "https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&fq0=metadataSource%3A%22Harvested%22&types=dataverses%3Adatasets&sort=nameSort&order=desc&page={page}"

dataset_dict = {}  

while True:
    html_filename = Path(f"data/interim/moissones/{page}.html")

    if html_filename.exists():
        print(f"Utilisation du cache HTML pour la page {page}")
        with open(html_filename, "r", encoding="utf-8") as file:
            html_text = file.read()
    else:
        print(f"Téléchargement de la page {page}")
        url = url_template.format(page=page)
        response = requests.get(url)
        html_text = response.text

        # Sauvegarde de la page HTML en local
        html_filename.parent.mkdir(parents=True, exist_ok=True)
        with open(html_filename, "w", encoding="utf-8") as file:
            file.write(html_text)

    # Analyse du HTML
    html = BeautifulSoup(html_text, "html.parser")
    jeu_de_donnees = html.find_all("div", class_="datasetResult clearfix")

    for jeu in jeu_de_donnees:
        titre_element = jeu.find("a", href=True)
        titre_jeu = titre_element.text.strip() if titre_element else "Titre inconnu"
        lien_jeu = titre_element["href"] if titre_element else None
        url_jeu = f"https://entrepot.recherche.data.gouv.fr{lien_jeu}" if lien_jeu else "URL inconnue"

        # Récupération de l'entrepôt
        balise_moisson = jeu.find("div", class_="text-muted small margin-top-half")
        if balise_moisson:
            texte_balise = balise_moisson.text.strip()
            liens = re.findall(r"https?://[^\s)]+", texte_balise)
            if liens:
                entrepot = re.split(r"https?://[^\s)]+", texte_balise, maxsplit=1)[0]
                
            else:
                # Trouver toutes les balises <span> contenant " - "
                span_balise = jeu.find("span", class_="text-muted", string=" - ")

                if span_balise:
                    # Chercher le lien <a> qui suit immédiatement
                    entrepot_lien = span_balise.find_next("a")

                    if entrepot_lien:
                        entrepot_nom = entrepot_lien.get_text(strip=True)  # Récupère le texte du lien
                        entrepot_url = entrepot_lien["href"]  # Récupère l'URL de l'entrepôt

                        # Si l'URL est relative, compléter avec le domaine de base
                        if entrepot_url.startswith("/"):
                            entrepot_url = f"https://entrepot.recherche.data.gouv.fr{entrepot_url}"

                        print(f"Entrepôt trouvé: {entrepot_nom} ({entrepot_url})")
                        # Nettoyage de l'entrepôt pour ne garder que le nom propre
                        
                        match = re.search(r"entrepôt partenaire\s*(\w+)", texte_balise)
                        if match:
                            entrepot = match.group(1)  # Extrait le nom de l'entrepôt après "entrepôt partenaire"
                        else:
                            entrepot = entrepot_nom  # Sinon, on garde le nom de l'entrepôt trouvé
                    else:
                        print("Aucun entrepôt trouvé après le <span>.")
                else:
                    print("Balise <span> introuvable.")

        # Ajouter les informations au dictionnaire
        dataset_dict[titre_jeu] = {"entrepôt": entrepot, "url": url_jeu}

    # Vérification pour arrêter la boucle
    if len(jeu_de_donnees) < 10:
        break

    page += 1

# **Écriture dans un fichier CSV**
csv_filename = Path("data/datasets_moissones.csv")
csv_filename.parent.mkdir(parents=True, exist_ok=True)

with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Titre du jeu de données", "Entrepôt", "URL"])  # En-tête

    for titre, info in dataset_dict.items():
        writer.writerow([titre, info["entrepôt"], info["url"]])

print(f"Les données ont été enregistrées dans {csv_filename}")

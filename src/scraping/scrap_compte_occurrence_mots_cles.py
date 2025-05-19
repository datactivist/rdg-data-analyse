import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from collections import Counter
import os

def extraire_fin_lien(lien):
    """Extrait la partie après le dernier slash dans un lien."""
    return os.path.basename(lien)

def extract_word_details(file_path, search_word):
    word_variants = r"({})(s|r|é|ée|és|ées|ness|y|ant|ants)?".format(re.escape(search_word))   
    
    df = pd.read_excel(file_path)
    results = []

    if "Lien" in df.columns:
        for link in df["Lien"].dropna():
            safe_link = extraire_fin_lien(link)
            filename = Path(f"data/interim/keywords/{safe_link}.html")
            html_text = ""

            if filename.exists():
                print("Used cached HTML")
                with open(filename, "r", encoding="utf-8") as file:
                    html_text = file.read()
                soup = BeautifulSoup(html_text, "html.parser")
            else:
                try:
                    response = requests.get(link, timeout=5)
                    if response.status_code == 200:
                        html_text = response.text
                        soup = BeautifulSoup(html_text, "html.parser")
                except Exception as e:
                    results.append({"lien": link, "champ": "Erreur", "forme": str(e), "occurrence": 0})
                    continue  # Passe au lien suivant

            # Gestion des pages Dataverse
            if "dataverse" in link:
                content = soup.find(id="dataverseDesc")
                if content:
                    text = content.get_text(strip=True)
                    matches = re.findall(word_variants, text, re.IGNORECASE)
                    counts = Counter([match[0] for match in matches]) 

                    for match, count in counts.items():
                        results.append({
                            "lien": link,
                            "champ": "dataverseDesc",
                            "forme": match,
                            "occurrence": count                                  
                        })

            # Gestion des pages Dataset
            elif "dataset" in link:
                metadata_rows = soup.select('table.metadata tbody tr')
                if metadata_rows:
                    for row in metadata_rows:
                        field = row.find('th').get_text(strip=True)
                        content = row.find('td').get_text(strip=True)
                        matches = re.findall(word_variants, content, re.IGNORECASE)

                        if matches and not any(entry["lien"] == link and entry["champ"] == field for entry in results):
                            results.append({
                                "lien": link,
                                "champ": field,
                                "forme": matches[0],  # Prend seulement la première occurrence trouvée
                                "occurrence": len(matches)  # Nombre total d'occurrences
                            })

                    # Analyse des fichiers liés aux datasets
                    files = soup.select('.ui-datatable-tablewrapper .col-file-metadata')
                    if files:
                        for file in files:
                            file_name = file.select_one('.fileNameOriginal')
                            file_desc = file.select_one('.fileDescription.small')

                            file_name_text = file_name.get_text(strip=True) if file_name else ""
                            file_desc_text = file_desc.get_text(strip=True) if file_desc else ""

                            # Vérification des mots-clés dans le nom du fichier
                            name_matches = re.findall(word_variants, file_name_text, re.IGNORECASE)
                            name_counts = Counter([match[0] for match in name_matches])

                            for match, count in name_counts.items():
                                # Vérification si cette combinaison lien-champ-forme existe déjà dans les résultats
                                if name_matches and not any(entry["lien"] == link and entry["champ"] == f"Nom du fichier: {file_name_text}" and entry["forme"] == match for entry in results):
                                    results.append({
                                        "lien": link,
                                        "champ": f"Nom du fichier: {file_name_text}",
                                        "forme": match,
                                        "occurrence": count
                                    })

                            # Vérification des mots-clés dans la description du fichier
                            desc_matches = re.findall(word_variants, file_desc_text, re.IGNORECASE)
                            desc_counts = Counter([match[0] for match in desc_matches])

                            for match, count in desc_counts.items():
                                # Vérification si cette combinaison lien-champ-forme existe déjà dans les résultats
                                if desc_matches and not any(entry["lien"] == link and entry["champ"] == f"Description du fichier: {file_name_text}" and entry["forme"] == match for entry in results):
                                    results.append({
                                        "lien": link,
                                        "champ": f"Description du fichier: {file_name_text}",
                                        "forme": match,
                                        "occurrence": count
                                    })


                else:  # Si pas de table metadata, analyser toute la page (avec seen_entries ici uniquement)
                    all_tags = soup.find_all()
                    for tag in all_tags:
                        tag_text = tag.get_text(strip=True)
                        if tag_text:
                            matches = re.findall(word_variants, tag_text, re.IGNORECASE)
                            counts = Counter([match[0] for match in matches])

                            for match, count in counts.items():
                                champ_info = f"{tag.name}: {tag_text[:50]}"  # Tronquer si trop long

                                # Vérifier si cette combinaison lien-champ-forme existe déjà dans les résultats
                                if matches and not any(entry["lien"] == link and entry["champ"] == champ_info and entry["forme"] == match for entry in results):
                                    results.append({
                                        "lien": link,
                                        "champ": champ_info,
                                        "forme": match,
                                        "occurrence": count
                                    })




            # Gestion des pages de fichiers
            elif "file" in link:
                text = soup.get_text()
                matches = re.findall(word_variants, text, re.IGNORECASE)
                counts = Counter([match[0] for match in matches])

                for match, count in counts.items():
                    results.append({
                        "lien": link,
                        "champ": "Contenu du fichier",
                        "forme": match,
                        "occurrence": count
                    })


            else:
                results.append({"lien": link, "champ": "Erreur HTTP", "forme": "", "occurrence": 0})

            # Écriture du fichier HTML en cache si HTML extrait
            if html_text:
                with open(f"data/interim/keywords/{safe_link}.html", "w", encoding="utf-8") as file:
                    file.write(html_text)

    return pd.DataFrame(results)

# Exécuter la fonction pour plusieurs mots-clés
search_words = ["alerte", "alert", "risque", "risk"]
for word in search_words:
    file_path = Path(f"extraction_resultats_{word}.xlsx")
    df_results = extract_word_details(file_path, word)
    output_path = Path(f"resultats_{word}_details.xlsx")
    df_results.to_excel(output_path, index=False)
    print(df_results.head())

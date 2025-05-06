import json
import pandas as pd
from keybert import KeyBERT
import re
from pathlib import Path
import langid

def remove_dates_and_years(text):
    """
    Fonction pour supprimer les dates et les années d'une description.
    Supprime les dates au format YYYY-MM-DD et les années seules (ex: 2022).
    """
    text = re.sub(r"\d{4}[-/]\d{2}[-/]\d{2}", "", text)  # Supprime les dates au format YYYY-MM-DD
    text = re.sub(r"\b\d{4}\b", "", text)  # Supprime les années seules (par exemple 2022)
    return text

def detect_language(text):
    return langid.classify(text)[0]

def extract_keywords_from_descriptions(json_file, csv_file):
    """
    Fonction pour extraire les mots-clés des descriptions d'un fichier JSON et les ajouter à un fichier CSV.
    
    Args:
        json_file (str): Chemin vers le fichier JSON contenant les descriptions des datasets.
        csv_file (str): Chemin vers le fichier CSV contenant les mots-clés existants.
        output_csv (str): Chemin vers le fichier CSV où les résultats seront sauvegardés.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)


    print(f"Nombre d'éléments dans le fichier JSON : {len(data)}")

    descriptions = []


    # Extraction des descriptions pertinentes (type == 'dataset' et lang == 'fr')
    for item in data:
        if item["type"] == "dataset" and item["lang"] == "fr":
            
            if not item.get("description"):  # Vérifie si la description est vide
                print(f"Erreur : description vide pour l'élément {item['name']}")
                continue

            descriptions.append(
                {
                    "identifier": item["global_id"][4:],  # Extrait l'ID sans le préfixe
                    "description": item["description"],
                    "title": item["name"]
                }
            )

        elif item["type"] == "dataset" and item["lang"] == "en":
            if not item.get("description"):
                print(f"Erreur : description vide pour l'élément {item['name']}")
                print(len(item["description"]))
                continue
            descriptions.append(
                {
                    "identifier": item["global_id"][4:],  # Extrait l'ID sans le préfixe
                    "description": item["description"],
                    "title": item["name"]
                })
        # get any missing descriptions in other languages
        elif item["type"] == "dataset" and item["lang"] not in ["fr", "en"]:
            if not item.get("description"):
                print(f"Erreur : description vide pour l'élément {item['name']}")
                continue
            descriptions.append(
                {
                    "identifier": item["global_id"][4:],  # Extrait l'ID sans le préfixe
                    "description": item["description"],
                    "title": item["name"]
                })

        

    # add title to descriptions
    for item in descriptions:
        item["description"] = item["title"] + " " + item["description"]
        
    print(f"Nombre de descriptions extraites : {len(descriptions)}")


    # ouvrir fichier terms.txt en anglais ou français 
  # Langue du fichier CSV
   # if item["lang"] == "fr":
    #    langue = "french"
    #    thesaurus_txt = Path(r"C:\Users\labo.adm\Documents\rdg\data\thesaurus\terms_fr.txt")
    #else:   
     #   thesaurus_txt = Path(r"C:\Users\labo.adm\Documents\rdg\data\thesaurus\terms_en.txt")
     #   langue = "english"
    #with open(thesaurus_txt, "r", encoding="utf-8") as f:
     #   thesaurus_read = f.readlines()
    # Liste des candidats pour l'extraction de mots-clés 
    #thesaurus = [line.strip() for line in thesaurus_read]
    
    # Initialisation du modèle KeyBERT
    model = KeyBERT("paraphrase-multilingual-MiniLM-L12-v2")

    # Extraction des mots-clés pour chaque description
    keywords_keybert = []
    for i, item in enumerate(descriptions):
        if i % 100 == 0:
            print(f"{i}/{len(descriptions)}")
        description = remove_dates_and_years(item["description"])  # Suppression des dates et années

        keywords_keybert.append(model.extract_keywords(description, top_n=5 ))  # Extraction des mots-clés
# paramètre  , ne fonctionne pas --> vectoriser les mots ?. Pb avec stop_words=langue aussi

    # Chargement du fichier CSV des mots-clés
    df = pd.read_csv(csv_file, encoding="utf-8", sep=";")


    # Ajout des mots-clés extraits au DataFrame
    df["keywords_keybert"] = keywords_keybert


    output_csv = csv_file.replace(".csv", f"_v2.csv")  # Chemin du fichier de sortie

    # Sauvegarde du DataFrame avec les mots-clés extraits dans le fichier de sortie
    df.to_csv(output_csv, index=False, encoding="utf-8",sep=";")
    print(f"Fichier mis à jour avec succès : {output_csv}")
    print(df.head())


# Exemple d'appel de la fonction
extract_keywords_from_descriptions("data/raw/rdg_corpus_with_lang.json", 
                                   "data/interim/keywords.csv")



# TODO : Tester plusieurs langues en même temps
# TODO : ignorer les dates
# TODO : tester keybert sur des thésaurus : chercher un thésaurus open source français / anglais | chercher thésaurus utilisés par rdg | générer un thésaurus à partir de la base de données rdg
# TODO : keybert au format notebook avec interface utilisateur pour entrer la description
# TODO : interface notebook : propose le top 3 des mots clés classiques, le top 2 des mots clés du ou des thésaurus + mettre un threshold de score

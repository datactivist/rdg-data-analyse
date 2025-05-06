from sklearn.feature_extraction.text import TfidfVectorizer
import json
import langid
import pandas as pd
import re

def remove_dates_and_years(text):
    # Expression régulière pour enlever les dates au format YYYY-MM-DD et les années seules (ex: 2022)
    text = re.sub(r"\d{4}[-/]\d{2}[-/]\d{2}", "", text)  # Supprime les dates au format YYYY-MM-DD
    text = re.sub(r"\b\d{4}\b", "", text)  # Supprime les années seules (par exemple 2022)
    return text

# Fonction pour détecter la langue
def detect_language(text):
    return langid.classify(text)[0]

with open("data/raw/rdg_corpus_with_lang.json", "r", encoding="utf-8") as f:
    data = json.load(f)

    # Détection de la langue pour les éléments qui n'ont pas de clé "lang"
    for item in data:
        if item["type"] == "dataset":
            # Si la clé "lang" est absente ou vide, on l'ajoute avec la langue détectée
            if not item.get("lang"):
                item["lang"] = detect_language(item["description"])

    print(len(data))  # Affiche la longueur des données après ajout de la langue

with open("data/raw/rdg_corpus_with_lang.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# Liste pour stocker les descriptions valides
descriptions = []

# Filtrage des descriptions valides
for item in data:
    if item["type"] == "dataset" :

        # Ajouter la description, même si elle est courte
        # Enlever les dates et les années
        item["description"] = remove_dates_and_years(item["description"])
        descriptions.append(
            {
                "identifier": item["global_id"][4:],  # Extraction de l'ID global
                "description": item["description"],
            }
        )

print(len(descriptions))  # Affiche le nombre de descriptions valides

# Filtrer les descriptions qui ne sont pas totalement vides après avoir retiré les mots vides
valid_descriptions = [desc["description"] for desc in descriptions if desc["description"].strip()]

if not valid_descriptions:
    raise ValueError("Aucune description valide à analyser, toutes les descriptions sont vides ou composées uniquement de mots vides.")

# Calcul du TF-IDF
vectorizer = TfidfVectorizer(stop_words=["le", "la", "les", "de", "des", "et", "à", "en", "un", "une", "dans", "pour", "the"])
tfidf_matrix = vectorizer.fit_transform(valid_descriptions)
feature_names = vectorizer.get_feature_names_out()

def get_top_n_keywords(tfidf_matrix, feature_names, n=5):
    # Obtenir les scores TF-IDF pour chaque document
    sorted_items = tfidf_matrix.sum(axis=0).A1.argsort()[::-1]
    top_keywords = [feature_names[i] for i in sorted_items[:n]]
    return top_keywords

# Création d'un dataframe avec les descriptions et les mots-clés
df = pd.DataFrame(
    {
        "identifier": [desc["identifier"] for desc in descriptions],
        "description": [desc["description"] for desc in descriptions],
        "keywords_tfidf": [
            get_top_n_keywords(tfidf_matrix[i], feature_names, n=5)
            for i in range(len(valid_descriptions))
        ],
    }
)

# Sauvegarde des résultats dans un fichier CSV
df.to_csv("data/interim/keywords.csv", index=False, encoding="utf-8", sep=";")
print(df.head())  # Affiche les 5 premières lignes du dataframe

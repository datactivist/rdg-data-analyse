from sklearn.feature_extraction.text import TfidfVectorizer
import json
import langid
import pandas as pd


# Function to detect language
def detect_language(text):
    return langid.classify(text)[0]


with open("data/interim/rdg_corpus_with_lang.json", "r", encoding="utf-8") as f:
    data = json.load(f)

    print(len(data))

    descriptions = []

    for item in data:
        if item["type"] == "dataset" and item["lang"] == "fr":
            if not item["description"] and len(item["description"]) < 30:
                print(f"Erreur : description vide pour l'élément {item['name']}")
                continue

            descriptions.append(
                {
                    "identifier": item["global_id"][4:],
                    "description": item["description"],
                }
            )

print(len(descriptions))

# Calculer le TF-IDF
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([desc["description"] for desc in descriptions])
feature_names = vectorizer.get_feature_names_out()

stop_words = [
    "le",
    "la",
    "les",
    "de",
    "des",
    "et",
    "à",
    "en",
    "un",
    "une",
    "dans",
    "pour",
    "the",
]


def get_top_n_keywords(tfidf_matrix, feature_names, n=5):
    # Obtenir les scores TF-IDF pour chaque document
    sorted_items = tfidf_matrix.sum(axis=0).A1.argsort()[::-1]
    top_keywords = [feature_names[i] for i in sorted_items[:n]]
    return [word for word in top_keywords if word not in stop_words]


# dataframe with description and keywords
df = pd.DataFrame(
    {
        "identifier": [desc["identifier"] for desc in descriptions],
        "description": [desc["description"] for desc in descriptions],
        "keywords_tfidf": [
            get_top_n_keywords(tfidf_matrix[i], feature_names, n=5)
            for i in range(len(descriptions))
        ],
    }
)

df.to_csv("data/interim/keywords.csv", index=False, encoding="utf-8")
print(df.head())

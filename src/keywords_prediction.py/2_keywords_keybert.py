import json
import pandas as pd
from keybert import KeyBERT

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

df = pd.read_csv("data/interim/keywords.csv", encoding="utf-8")

model = KeyBERT("paraphrase-multilingual-MiniLM-L12-v2")

keywords_keybert = []
for i, item in enumerate(descriptions):

    if i % 100 == 0:
        print(f"{i}/{len(descriptions)}")

    description = item["description"]
    keywords_keybert.append(model.extract_keywords(description, top_n=5))


df["keywords_keybert"] = keywords_keybert

df.to_csv("data/interim/keywordsv2.csv", index=False, encoding="utf-8")
print(df.head())


# TODO : Tester plusieurs langues en même temps
# TODO : ignorer les dates
# TODO : tester keybert sur des thésaurus : chercher un thésaurus open source français / anglais | chercher thésaurus utilisés par rdg | générer un thésaurus à partir de la base de données rdg
# TODO : keybert au format notebook avec interface utilisateur pour entrer la description
# TODO : interface notebook : propose le top 3 des mots clés classiques, le top 2 des mots clés du ou des thésaurus + mettre un threshold de score

from sentence_transformers import SentenceTransformer, util
import pandas as pd
from pathlib import Path
import langid

# Chargement du modèle (+ trouver un modèle fr)
model_1 = SentenceTransformer("distiluse-base-multilingual-cased-v1")
model_2 = SentenceTransformer("sentence-transformers/LaBSE")
model_3 = SentenceTransformer("multi-qa-mpnet-base-cos-v1")

# Dossier des thésaurus
thesaurus_dir = Path("data/thesaurus/processed")
thesaurus_files = thesaurus_dir.glob("*.csv")

# Fonction pour charger les thésaurus par langue
def load_thesaurus_and_encode(thesaurus_file):
    df = pd.read_csv(thesaurus_file, encoding="utf-8")[["fr", "en"]].dropna()
    data = {}

    for lang in ["fr", "en"]:
        terms = df[lang].dropna().tolist()
        embeddings = model_3.encode(terms, convert_to_tensor=True)
        data[lang] = {
            "candidates": terms,
            "embeddings": embeddings
        }

    return data

# Chargement des thésaurus
thesaurus_data = {}
for file in thesaurus_files:
    name = file.stem
    thesaurus_data[name] = load_thesaurus_and_encode(file)

print(f"Thésaurus chargés : {list(thesaurus_data.keys())}")

# Chargement des descriptions
df = pd.read_csv("data/interim/keywords_v2.csv", encoding="utf-8", sep=";")

# Détection de la langue
df["lang"] = df["description"].apply(lambda x: langid.classify(x)[0])

# Fonction principale de prédiction
def predict_keywords(doc, lang, thesaurus_data, n=5, threshold=0.25):
    if lang not in ["fr", "en"]:
        lang = "fr"  # fallback
    doc_embedding = model_3.encode(doc, convert_to_tensor=True)

    results_by_thesaurus = {}
    all_keywords = []

    for thesaurus_name, data in thesaurus_data.items():
        if lang not in data:
            continue

        candidates = data[lang]["candidates"]
        embeddings = data[lang]["embeddings"]
        scores = util.cos_sim(doc_embedding, embeddings)[0]

        thesaurus_results = []
        for kw, score in zip(candidates, scores):
            score_val = float(score)
            if score_val >= threshold:
                thesaurus_results.append((kw, score_val))
                all_keywords.append((kw, score_val, thesaurus_name))

        # Top n pour ce thésaurus
        thesaurus_results = sorted(thesaurus_results, key=lambda x: x[1], reverse=True)[:n]
        results_by_thesaurus[thesaurus_name] = thesaurus_results

    # Top n global
    top_all = sorted(all_keywords, key=lambda x: x[1], reverse=True)[:n]

    return results_by_thesaurus, top_all

# Appliquer la prédiction
all_structs = []
all_tops = []

for _, row in df.iterrows():
    results_struct, top_all = predict_keywords(row["description"], row["lang"], thesaurus_data)
    all_structs.append(results_struct)
    all_tops.append(top_all)

df["predicted_keywords_struct"] = all_structs

# Colonnes par thésaurus
for thesaurus_name in thesaurus_data.keys():
    df[thesaurus_name] = df["predicted_keywords_struct"].apply(
        lambda x: "; ".join(kw for kw, _ in x.get(thesaurus_name, []))
    )

# Colonne finale top_5_keywords (avec score + nom thésaurus)
df["top_5_keywords"] = all_tops = [
    "; ".join(f"{kw} ({score:.2f}) [{thesaurus}]" for kw, score, thesaurus in top)
    for top in all_tops
]

# Sauvegarde
output_path = Path("data/interim/keywords_predicted_M3.csv")
df.to_csv(output_path, index=False, encoding="utf-8", sep=";")
print(f"Résultats sauvegardés dans {output_path}")


# TODO : normalize_term : enlève les accents, on veut garder les accents
# TODO : charger également le thésaurus en français pour les documents en français
# TODO : faire la récupération de mots clés sur tout les documents (en incluant le titre)
# TODO : Sauvegarder le tuple : (document, mots clés)
# TODO : tester fr/en avec le même modèle ou besoin d'avoir un modèle spécifique
# TODO : une fois qu'on a une liste de mots-clés, récupérer les équivalents dans l'autre langue
# --------------------------------------------------------
# TODO : faire la même chose avec le modèle de KeyBERT en étape 1 (d'abord vérifier si pertinent) ;
# en donnant les mots clés retourné par keybert à predict_n_keywords_from_doc plutôt que la description complète
# Sauvegarder dans un fichier au même endroit que la méthode initial (titre, description, mots_clés_description, mots_clés_keybert)

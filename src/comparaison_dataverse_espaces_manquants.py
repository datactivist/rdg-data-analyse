import csv
import json
from pathlib import Path

# On charge les fichiers à comparer
# espace_file = Path("espaces_institutionnels_collections.csv")
categorie_file = Path("data/interim/dataverse_type.csv")
espace_institutionnel_file = Path(
    "data/interim/espaces_institutionnels_identifiers.csv"
)
dataverses_file = Path("data/interim/dataverses.csv")
corpus_file = Path("data/raw/rdg_corpus.json")


def lire_identifiants_csv(file):
    identifiants = set()

    if not file.exists():  # Vérifier que le fichier existe
        print(f"Erreur : fichier {file} introuvable.")
        return identifiants

    if file.suffix == ".csv":  # Lecture d'un CSV
        with open(file, "r", encoding="utf-8") as f:
            lecteur = csv.DictReader(f)
            for ligne in lecteur:
                identifiant = ligne.get(
                    "identifier"
                )  # Utilisation de .get() pour éviter KeyError
                if identifiant:
                    identifiants.add(identifiant)
                else:
                    print(
                        f"Avertissement : clé 'identifier' absente dans la ligne CSV : {ligne}"
                    )
    return identifiants


def lire_identifiants_json(file, type):
    identifiants = set()
    if file.suffix == ".json":  # Lecture d'un JSON
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if (
                        isinstance(item, dict) and item.get("type") == type
                    ):  # Filtrage par type
                        identifiant = item.get(
                            "identifier"
                        )  # Utilisation de .get() pour éviter KeyError
                        if identifiant:
                            identifiants.add(identifiant)
                        else:
                            print(
                                f"Avertissement : clé 'identifier' absente dans l'élément JSON : {item}"
                            )
            else:
                print("Erreur : Le fichier JSON n'est pas un dictionnaire.")

    else:
        print(f"Format non supporté pour {file}")

    return identifiants


# Chargement des identifiants depuis les fichiers
# identifiants_espace = lire_identifiants_csv(espace_file)
identifiants_categorie = set(lire_identifiants_csv(categorie_file))
identifiants_espace_instit = set(lire_identifiants_csv(espace_institutionnel_file))
identifiants_dataverses = set(lire_identifiants_csv(dataverses_file))

# Comparaison corpus avec identifiants manquants (uniquement pour les éléments 'dataverse')
identifiants_corpus = set(lire_identifiants_json(corpus_file, "dataverse"))

all_identifiers = (
    identifiants_corpus.union(identifiants_categorie)
    .union(identifiants_dataverses)
    .union(identifiants_espace_instit)
)

common_identifiers = (
    identifiants_corpus.intersection(identifiants_categorie)
    .intersection(identifiants_dataverses)
    .intersection(identifiants_espace_instit)
)

# garder uniquement les identifiants qui ne sont pas dans les 3 listes
identifiants_diffs = all_identifiers - common_identifiers

done_identifiers = set()
with open("identifiants_diffs.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow(
        [
            "identifier",
            "api-corpus",
            "dataverses-scrapping",
            "category-scrapping",
            "espace-instit-scrapping",
        ]
    )  # En-tête

    for identifier in identifiants_diffs:
        if identifier in done_identifiers:
            continue
        done_identifiers.add(identifier)
        writer.writerow(
            [
                identifier,
                "X" if identifier in identifiants_corpus else "",
                "X" if identifier in identifiants_dataverses else "",
                "X" if identifier in identifiants_categorie else "",
                "X" if identifier in identifiants_espace_instit else "",
            ]
        )

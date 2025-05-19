import pandas as pd
from pathlib import Path
from Levenshtein import distance as levenshtein_distance

# Définition des chemins des fichiers
file_dataverse = Path(r"data/interim/dataverses_.csv")
file_keywords = Path(r"data/datasets_keywords.csv")

# Charger les fichiers avec gestion des erreurs
df_dataverse = pd.read_csv(file_dataverse, encoding="utf-8", dtype=str, on_bad_lines="skip")
df_keywords = pd.read_csv(file_keywords, encoding="ISO-8859-1", dtype=str, on_bad_lines="skip")

# Nettoyer les noms de colonnes (supprimer espaces cachés)
df_dataverse.columns = df_dataverse.columns.str.strip()
df_keywords.columns = df_keywords.columns.str.strip()

# Afficher les colonnes disponibles
print("Colonnes disponibles dans df_keywords :", df_keywords.columns.tolist())
print("Colonnes disponibles dans df_dataverse :", df_dataverse.columns.tolist())

# Vérifier la présence des colonnes requises DANS CHAQUE DATAFRAME INDÉPENDAMMENT
missing_columns_keywords = [col for col in ['keyword'] if col not in df_keywords.columns]
missing_columns_dataverse = [col for col in ['Nom du Dataverse'] if col not in df_dataverse.columns]

# Lever une erreur explicite si une colonne manque
if missing_columns_keywords:
    raise KeyError(f"Les colonnes suivantes sont absentes de df_keywords : {missing_columns_keywords}")
if missing_columns_dataverse:
    raise KeyError(f"Les colonnes suivantes sont absentes de df_dataverse : {missing_columns_dataverse}")

# Extraction des données non nulles
keywords = df_keywords['keyword'].dropna().tolist()
dataverse = df_dataverse['Nom du Dataverse'].dropna().tolist()

# Comparaison et calcul de similarité
results = []
lowercase_matches = set()
exact_matches = set()

for nom in dataverse:
    nom_lower = nom.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        if keyword_lower == nom_lower:
            lowercase_matches.add(nom_lower)
        
        if keyword == nom:
            exact_matches.add(keyword)

        # Calcul de la distance de Levenshtein
        distance = levenshtein_distance(keyword_lower, nom_lower)
        if distance < 1:  
            results.append([keyword, nom, distance])

# Sauvegarde des résultats
df_results = pd.DataFrame(results, columns=['Keyword', 'Nom du Dataverse', 'Distance'])
output_file = Path(r"data/interim/similar_keywords.csv")
df_results.to_csv(output_file, index=False, encoding="utf-8")

print(f"Les résultats ont été sauvegardés dans {output_file}")
print("Exact matches :", list(exact_matches))

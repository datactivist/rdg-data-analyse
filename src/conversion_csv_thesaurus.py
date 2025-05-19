from pathlib import Path
from rdflib import Graph, term
from rdflib.namespace import SKOS
import pandas as pd

# Liste des thésaurus et leurs chemins
thesaurus_paths = {
    "unesco": Path('C:/Users/labo.adm/Documents/rdg/data/thesaurus/unesco-thesaurus.rdf'),
    "elsst": Path('C:/Users/labo.adm/Documents/rdg/data/thesaurus/ELSST_R5.rdf'),
    "agrovoc": Path('C:/Users/labo.adm/Documents/rdg/data/thesaurus/agrovoc.rdf'),
    "inrae": Path('C:/Users/labo.adm/Documents/rdg/data/thesaurus/thesaurusINRAE.rdf')
}

# Fonction pour extraire les termes associés au même concept
def extract_aligned_terms(thesaurus_file):
    g = Graph()
    g.parse(thesaurus_file, format="xml")
    
    concepts = {}

    for s, p, o in g:
        if p == SKOS.prefLabel and isinstance(o, term.Literal):
            lang = o.language
            label = o.value
            
            if s not in concepts:
                concepts[s] = {}
            
            if lang == "fr":
                concepts[s]["fr"] = label
            elif lang == "en":
                concepts[s]["en"] = label

    return concepts

# Dossier de sortie
output_dir = Path("C:/Users/labo.adm/Documents/rdg/data/thesaurus/processed")
output_dir.mkdir(parents=True, exist_ok=True)

# Parcourir chaque thésaurus
for name, path in thesaurus_paths.items():
    print(f"Extraction du thésaurus : {name}")

    concepts = extract_aligned_terms(path)

    rows = []
    for uri, labels in concepts.items():
        fr = labels.get("fr", "")
        en = labels.get("en", "")
        
        # Ajouter uniquement si au moins une des deux langues est disponible
        if fr or en:
            rows.append({
                "fr": fr,
                "en": en
            })

    df = pd.DataFrame(rows)

    # Définir le fichier de sortie
    output_file = output_dir / f"{name}_terms.csv"

    # Sauvegarder en CSV
    df.to_csv(output_file, index=False, encoding="utf-8")
    
    print(f"--> Sauvegardé dans {output_file}")

print("Extraction terminée pour tous les thésaurus.")

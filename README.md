# Analyse des métadonnées présentes dans l'entrpôt de données RDG

## Prérequis

- Python 3.8 ou supérieur

## Installation

Créer un environnement virtuel :

```bash
python -m venv env
```

Activer l'environnement virtuel :

```bash
source env/bin/activate # Linux
env\Scripts\activate # Windows
```

Installer les dépendances avec pip :

```bash
pip install -r requirements.txt
```

## Utilisation

### Extract data

Extract the data from the RDG API.

```bash
python src/extract_rdg_corpus.py
```

### Separate types

This script will separate the data into 3 files : one for each type (files, datasets, dataverse).

```bash
python src/filter_types.py
```

### Analyse metadata

Le notebook `notebooks/analyse_rdg_metadata.ipynb` permet d'analyser les métadonnées des fichiers, jeux de données et dataverses.

Vous pouvez le lancez via VSCode (avec l'extension Jupyter) ou via Juptyer Notebook.

## Données

Les données dans ce dépôt ont été extraite à date du 2024-10-02.

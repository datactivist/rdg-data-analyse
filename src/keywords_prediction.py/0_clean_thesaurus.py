# Pas de doublon :
# exact, sans accents, sans majuscules, pluriel, féminin, etc..
import unicodedata




with open("data/thesaurus/terms_en.txt", "r", encoding="utf-8") as f:
    en_candidates = f.read().splitlines()

with open("data/thesaurus/terms_fr.txt", "r", encoding="utf-8") as f:
    fr_candidates = f.read().splitlines()


def normalize_term(term):
    """
    Normalizes a term by removing accents and converting to lowercase.

    Args:
        term (str): The term to normalize.

    Returns:
        str: The normalized term.
    """
    # Remove accents and convert to lowercase
    normalized_term = unicodedata.normalize("NFD", term).lower()
    return normalized_term


def clean_thesaurus(thesaurus):
    """ 
    Cleans a thesaurus by removing duplicates and normalizing the terms.

    Args:
        thesaurus (list): A list of terms to clean.

    Returns:
        list: A cleaned list of terms.
    """
    # Remove duplicates
    thesaurus = [normalize_term(term) for term in thesaurus]
    thesaurus = list(set(thesaurus))

    return thesaurus

en_cleaned_thesaurus = clean_thesaurus(en_candidates)


with open("data/thesaurus/cleaned_terms_en.txt", "w", encoding="utf-8") as f:
    for term in en_cleaned_thesaurus:
        f.write(term + "\n")


fr_cleaned_thesaurus = clean_thesaurus(fr_candidates)
with open("data/thesaurus/cleaned_terms_fr.txt", "w", encoding="utf-8") as f:
    for term in fr_cleaned_thesaurus:
        f.write(term + "\n")   
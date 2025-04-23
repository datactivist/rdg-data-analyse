from sentence_transformers import SentenceTransformer, util
import unicodedata

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

# load data/thesaurus/terms_en.txt
with open("data/thesaurus/cleaned_terms_en.txt", "r", encoding="utf-8") as f:
    candidates = f.read().splitlines()


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


def embed_thesaurus(model, thesaurus):
    """
    Embeds a list of keywords using a pre-trained model.

    Args:
        thesaurus (list): A list of keywords to embed.

    Returns:
        list: A list of embeddings for the keywords.
    """
    return model.encode(thesaurus, convert_to_tensor=True)


def predict_n_keywords_from_doc(doc, n=5, candidates_embeddings=None, threshold=0.5):
    """
    Predicts the top n keywords from a document using a list of candidates.

    Args:
        doc (str): The document to analyze.
        n (int): The number of keywords to predict.
        candidates (list): A list of embedded candidate keywords.
        threshold (float): The threshold for cosine similarity.

    Returns:
        list: A list of the top n predicted keywords.
    """

    doc_embedding = model.encode(doc, convert_to_tensor=True)

    # find the top n most similar candidates to the document
    top_n = min(n, len(candidates))
    cos_scores = util.cos_sim(doc_embedding, candidates_embeddings)[0]

    results = list(zip(candidates, cos_scores.cpu().numpy()))

    results = [r for r in results if r[1] > threshold]

    results = sorted(results, key=lambda x: x[1], reverse=True)[:top_n]

    print(results)

    return [r[0] for r in results]


candidates_embeddings = embed_thesaurus(model, candidates)

test_doc = "The WP1 Gendered Food Product Profile for Fufu in Nigeria reflects the final step (step 5) of an interdisciplinary five-step methodology developed to identify demand for quality characteristics among diverse user groups along the food chain (Forsythe et al., 2022). This methodology includes: step 1) interdisciplinary state of knowledge of the product ; step 2) gendered food mapping, which includes participatory research with men and women in rural communities regarding their product preferences and priorities; step 3) participatory processing diagnosis and quality characteristics ; and step 4) consumer studies in rural and urban areas of the product using different RTB varieties. Results from step 1 and 2 have been published in Ugo Chijioke, Tessy Madu, Benjamin Okoye, Amaka Promise Ogunka, Mercy Ejechi, Miriam Ofoeze, Chukwudi Ogbete, Damian Njoku, Justin Ewuziem, Confidence Kalu, Nnaemeka Onyemauwa, Blessing Ukeje, Oluchi Achonwa, Lora Forsythe, Genevi\u00e8ve Fliedel & Chiedozie Egesi (2021). Quality attributes of fufu in South-East Nigeria: guide for cassava breeders. International Journal of Food science and Technology, 56(3), 1247-1257. https://doi.org/10.1111/ijfs.14875. The WP1 Gendered Food Product Profile for Fufu in Nigeria has been agreed by a multidisciplinary team based on the evidence collected on preferred quality characteristics at each step and assessed for their potential harm and benefit for women, based on an adapted G+ tool (publication pending by Forsythe et al.) Fufu processing is mainly conducted at the local and household level. Alternative crop uses of cassava are : sale of fresh roots, gari, and tapioca. Consumers of fufu are mainly from households and in the restaurants, with more consumption in rural areas compared to urban areas. Imo and Abia States have different processing steps and result in pounded or stirred Fufu, respectively and thus different consumers. The market demand for Fufu is significant given that people in the region consume it regularly, particularly in rural areas. Market demand for Fufu is expected to increase substantially in the next ten years, and will command a higher market price, especially the white/cream type. Results also show most preferred characteristics as mouldability/drawability and colour. At the raw material level, important quality characteristics for all users (women, men and youth) include; smooth skin, heavy weight, and white colour. Important processing characteristics were easy to ferment, easy to peel, high mash yield, and white/cream colour. At ready to eat stage, important characteristics of the Fufu product were, white/cream colour, easy to form dough and drawability. Poor quality characteristics indicated by the respondents during processing include: bad colour, light weight, fibrous/burnt cassava root, high moisture content, black lines on the body of the product, too soft, sticks to the hand, not easy to mould, not well cooked, and bad odour. Inferior varieties indicated were TMS 01/1412 and TMS/01/1368 as they were disliked in the 2 States (roots had high moisture content), less weight, less starch, poor fermentation, floating in water and yellow colour of Fufu. Varieties that were valued highly include: Nwaocha, and TMS 98/0505 at all levels (raw material, processing and ready to eat) and TME 419 at the raw material and processing levels. The Gender and livelihoods assessment resulted in the prioritization of several characteristics for WP2: white, easy to peel, rettiability, high Fufu mash yield and drawability of the final product."

test_doc = normalize_term(test_doc)

keyword_keybert = []

keywords = predict_n_keywords_from_doc(
    "keyword1 keyword2 keyword3",
    n=10,
    candidates_embeddings=candidates_embeddings,
    threshold=0.15,
)

print(keywords)

# TODO : normalize_term : enlève les accents, on veut garder les accents
# TODO : charger également le thésaurus en français pour les documents en français
# TODO : faire la récupération de mots clés sur tout les documents (en incluant le titre)
# TODO : Sauvegarder le tuple : (document, mots clés)
# TODO : tester fr/en avec le même modèle ou besoin d'avoir un modèle spécifique
# TODO : une fois qu'on a une liste de mots-clés, récupérer les équivalents dans l'autre langue
# --------------------------------------------------------
# TODO : faire la même chose avec le modèle de KeyBERT en étape 1 ;
# en donnant les mots clés retourné par keybert à predict_n_keywords_from_doc plutôt que la description complète
# Sauvegarder dans un fichier au même endroit que la méthode initial (titre, description, mots_clés_description, mots_clés_keybert)

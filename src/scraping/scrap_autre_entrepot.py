import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path

# URL de la page
#url_google_alert = Path("C:/Users/labo.adm/Documents/rdg/data/html_google/Dataset_Search_alert.htm")
#url_google_alerte = ""
url_google_risque = Path("C:/Users/labo.adm/Documents/rdg/data/html_google/Dataset_Search_risque.htm")
#url_google_risk = Path("C:/Users/labo.adm/Documents/rdg/data/html_google/Dataset_Search_risk.htm")

def scrape_google_dataset(url, output_csv):
    # Envoyer une requête GET
    with url.open(encoding="utf-8") as file:
        html_content = file.read()
        
    soup = BeautifulSoup(html_content, "html.parser")

    # Trouver toutes les balises li avec la classe "UnWQ5"
    balises = soup.find_all("li", class_="UnWQ5")

    if not balises:
        print("Aucune balise trouvée avec la classe 'UnWQ5'.")
        return

    print(f"{len(balises)} balises trouvées.")

    # Stocker les données
    data_list = []

    for balise in balises:
        dataset_element = balise.find("h1", class_="iKH1Bc")
        print(dataset_element)
        entrepot_element = balise.find("li", class_="iW1HZe")

        dataset_text = dataset_element.text.strip() if dataset_element else "Dataset not found"
        entrepot_text = entrepot_element.text.strip() if entrepot_element else "Entrepot not found"

        data_list.append([dataset_text, entrepot_text])

    # Sauvegarder les résultats dans un fichier CSV
    with open(Path(f"rdg/data/autre_entrepot{output_csv}"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Dataset", "Entrepot"])
        writer.writerows(data_list)

    print(f"Scraping terminé. Données sauvegardées dans {output_csv}")

#scrape_google_dataset(url_google_alert, "alert.csv")
#scrape_google_dataset(url_google_alerte, "alerte.csv")
#scrape_google_dataset(url_google_risque, "risque.csv")
#scrape_google_dataset(url_google_risk, "risk.csv")



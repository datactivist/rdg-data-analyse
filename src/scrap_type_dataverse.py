from bs4 import BeautifulSoup
import requests
from pathlib import Path

dataverse_type = [
    "Research Project",
    "Laboratory",
    "Research Group",
    "Organization or Institution",
    "Researcher",
    "Department",
    "Journal",
    "Teaching Course",
]


def extract_identifier_from_href(href):

    if "jsessionid" in href:
        href = href.split(";")[0]

    return href.split("/")[-1]


for d_type in dataverse_type:

    page = 1

    while True:

        html_filename = Path(f"data/interim/html/{d_type}_{page}.html")

        if html_filename.exists():
            print("Used cached HTML")
            with open(html_filename, "r", encoding="utf-8") as file:
                html_text = file.read()
                html = BeautifulSoup(html_text, "html.parser")
        else:
            url_template = "https://entrepot.recherche.data.gouv.fr/dataverse/root?q=&fq0=dvCategory%3A%22{metaverse_type}%22&types=dataverses%3Adatasets&sort=dateSort&order=desc&page={page}"
            url = url_template.format(
                metaverse_type=d_type.replace(" ", "+"), page=page
            )

            response = requests.get(url)

            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                continue

            html_text = response.text
            html = BeautifulSoup(html_text, "html.parser")

        table = html.find("table", {"id": "resultsTable"})
        tds = table.find_all("td")

        identifiers = []
        for td in tds:
            title = td.find("div", {"class": "card-title-icon-block"})
            href = title.find("a")["href"]
            identifier = extract_identifier_from_href(href)
            identifiers.append(identifier)

        with open(
            f"data/interim/html/{d_type}_{page}.html", "w", encoding="utf-8"
        ) as file:
            file.write(html_text)

        if len(identifiers) != 10:
            break

        page += 1

# TODO
# Sauvegarder dans un fichier data/interim/dataverse_type.csv
# Utiliser le fichier data/interim/dataverse_type.csv pour ajouter les types de dataverses dans rdg_corpus.json (en le renommant rdg_corpus_extended.json)

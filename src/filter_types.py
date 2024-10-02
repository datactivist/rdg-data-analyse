import json
import requests
from pathlib import Path
import pandas as pd


input_data_path = Path("data/raw")
input_data_path.mkdir(parents=True, exist_ok=True)
output_data_path = Path("data/interim")
output_data_path.mkdir(parents=True, exist_ok=True)

input_data = input_data_path / Path("rdg_corpus.json")

file_types = ["file", "dataset", "dataverse"]

metadata_mapping = {
    "file": [
        "name",
        # "type",
        "url",
        # "file_id",
        "file_persistent_id",
        "description",
        "dataset_name",
        "dataset_id",
        "dataset_persistent_id",
        # "dataset_citation",
        "published_at",
        "file_type",
        "file_content_type",
        "size_in_bytes",
        # "md5",
        # "checksum",
        # "unf",
    ],
    "dataset": [
        "name",
        # "type",
        "url",
        # "global_id",
        "description",
        # "createdAt",
        "published_at",
        "updatedAt",
        "publisher",
        # "citation",
        # "citationHtml",
        "authors",
        "producers",
        "contacts",
        "name_of_dataverse",
        "identifier_of_dataverse",
        # "storageIdentifier",
        # "dataSources",
        "keywords",
        "subjects",
        # "publications",
        # "geographicCoverage",
        # "relatedMaterial",
        "fileCount",
        # "versionId",
        # "versionState",
        # "majorVersion",
        # "minorVersion",
    ],
    "dataverse": [
        "name",
        # "type",
        "url",
        "identifier",
        "description",
        "published_at",
    ],
}


with open(input_data, "r") as f:
    datasets = json.load(f)


for file_type in file_types:

    # filter datasets
    filtered_datasets = []

    for dataset in datasets:
        if dataset["type"] == file_type:
            filtered_datasets.append(dataset)

    # save filtered datasets
    df = pd.DataFrame(filtered_datasets)

    # only keep some columns
    df = df[metadata_mapping[file_type]]

    output_file = output_data_path / Path(f"rdg_corpus_{file_type}s.csv")

    df.to_csv(output_file, index=False)

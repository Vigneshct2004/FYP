import pandas as pd
import os

DATASET_PATH = r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\LJSpeech-1.1\LJSpeech-1.1"

metadata = pd.read_csv(
    os.path.join(DATASET_PATH, "metadata.csv"),
    sep="|",
    header=None
)

metadata.columns = ["id", "text", "normalized"]

print(metadata.head())
print("Total samples:", len(metadata))
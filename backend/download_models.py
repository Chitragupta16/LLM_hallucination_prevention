import spacy
import os

def download_models():
    try:
        spacy.load("en_core_web_sm")
        print("✓ spaCy model already downloaded")
    except:
        print("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_sm")
        print("✓ spaCy model downloaded")

if __name__ == "__main__":
    download_models()
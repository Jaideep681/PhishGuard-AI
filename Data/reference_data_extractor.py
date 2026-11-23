
"""
PHISHGUARD AI
REFERENCE DATA FEATURE EXTRACTOR
Extracts three reference-dependent features:
- TLDLegitimateProb
- URLCharProb
- URLSimilarityIndex
Reference source:
Original PhiUSIIL CSV dataset.
Method:
- TLD legitimacy is estimated from legitimate dataset records.
- URL character probability is estimated from character frequencies
  in legitimate URLs.
- URL similarity is estimated by comparing the submitted URL
  with sampled legitimate URLs.
IMPORTANT:
These are provisional statistical estimates.
They are NOT confirmed reproductions of the original
PhiUSIIL feature-generation formulas.
"""

import pandas as pd
import re
import os
import math
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import urllib.parse
from urllib.parse import urlsplit
from difflib import SequenceMatcher
from collections import Counter

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "Credentials.env"
load_dotenv(dotenv_path=ENV_PATH)

# MySQL configuration
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = int(os.getenv("DB_PORT", "3306"))
DATABASE = os.getenv("DB_NAME")
TABLE_NAME = os.getenv("DB_TABLE")

# Validate credentials
required_variables = {
    "DB_USER": USER,
    "DB_PASSWORD": PASSWORD,
    "DB_HOST": HOST,
    "DB_NAME": DATABASE,
    "DB_TABLE": TABLE_NAME
}
missing = [
    key for key, value in required_variables.items()
    if not value
]
if missing:
    raise ValueError(
        f"Missing environment variables: {', '.join(missing)}"
    )
safe_password = urllib.parse.quote_plus(PASSWORD)

#Connect engine to MySQL DataBase
connection_string = URL.create(
    drivername="mysql+mysqlconnector",
    username=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT,
    database=DATABASE
)
engine = create_engine(connection_string)

# Test MySQL connection
try:
    with engine.connect() as connection:
        print("MySQL connection successful!")

except Exception as error:
    print("MySQL connection failed:", error)
    engine.dispose()
    raise

class ReferenceDataExtractor:
    def __init__(self, legitimate_label, sample_size=5000):
        self.legitimate_label = legitimate_label
        self.sample_size = sample_size
        query = f"SELECT URL, label FROM {TABLE_NAME}"

        #Read the Execute statement of MySQL
        df = pd.read_sql(query, engine)
        required = {"URL", "label"}
        if not required.issubset(df.columns):
            raise ValueError("Dataset must contain URL and label columns")
        legitimate = df[
            df["label"] == legitimate_label
        ].dropna(subset=["URL"])
        if legitimate.empty:
            raise ValueError("No legitimate URL records found")
        self.legitimate_urls = (
            legitimate["URL"].astype(str).tolist()
        )

        # Prepare a manageable reference sample
        self.reference_urls = self.legitimate_urls[:sample_size]

        # Build TLD statistics
        self.tld_counts = Counter()
        self.tld_total = Counter()
        for url in self.legitimate_urls:
            tld = self.get_tld(url)
            if tld:
                self.tld_counts[tld] += 1
        for url in df["URL"].dropna().astype(str):
            tld = self.get_tld(url)
            if tld:
                self.tld_total[tld] += 1

        # Build legitimate URL character frequencies
        self.char_counts = Counter()
        for url in self.legitimate_urls:
            for char in url.lower():
                self.char_counts[char] += 1
        self.total_chars = sum(self.char_counts.values())
        print("Reference dataset loaded successfully.")
        print("Legitimate URLs:", len(self.legitimate_urls))
        print("Similarity sample:", len(self.reference_urls))

    @staticmethod
    def get_tld(url):
        try:
            value = url if "://" in url else "https://" + url
            hostname = urlsplit(value).hostname
            if hostname:
                return hostname.lower().rstrip(".").split(".")[-1]
        except ValueError:
            pass
        return None

    @staticmethod
    def normalize_url(url):
        return url.strip().lower()

    def tld_legitimate_probability(self, url):
        tld = self.get_tld(url)
        if not tld or self.tld_total[tld] == 0:
            return 0.0
        probability = (self.tld_counts[tld] / self.tld_total[tld]) * 100
        return round(probability, 4)

    def url_character_probability(self, url):
        if not self.total_chars:
            return 0.0
        value = self.normalize_url(url)
        probabilities = [
            self.char_counts[char] / self.total_chars
            for char in value
            if char in self.char_counts
        ]
        if not probabilities:
            return 0.0

        # Geometric mean of character frequencies
        score = math.exp(
            sum(math.log(p) for p in probabilities)/ len(probabilities)
        )
        return round(score * 100, 4)

    def url_similarity_index(self, url):
        target = self.normalize_url(url)
        if not target:
            return 0.0
        best_score = 0.0
        for reference in self.reference_urls:
            score = SequenceMatcher(
                None,
                target,
                self.normalize_url(reference)
            ).ratio()
            best_score = max(best_score, score)
        return round(best_score * 100, 4)

    def extract(self, url):
        return {
            "TLDLegitimateProb": self.tld_legitimate_probability(url),
            "URLCharProb": self.url_character_probability(url),
            "URLSimilarityIndex": self.url_similarity_index(url)
        }

# Testing
if __name__ == "__main__":
    LEGITIMATE_LABEL = 1
    try:
        extractor = ReferenceDataExtractor(
            legitimate_label=LEGITIMATE_LABEL
        )
        test_url = input("Enter URL: ").strip()
        result = extractor.extract(test_url)
        print("\nREFERENCE DATA FEATURES")
        print("=" * 40)
        for name, value in result.items():
            print(f"{name}: {value}")
        print("\nTotal reference features:", len(result))
    except Exception as error:
        print("Error:", error)

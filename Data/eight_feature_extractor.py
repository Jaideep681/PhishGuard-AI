"""
Stage 8: Additional Webpage Feature Extraction
Features:
- HasDescription
- URLTitleMatchScore
- Bank
- Pay
- Crypto
Uses the secure webpage-fetching function from Stage 5.
"""

import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from five_feature_extractor import fetch_webpage
BANK_WORDS = {"bank", "banking", "account"}
PAY_WORDS = {"pay", "payment", "checkout", "billing"}
CRYPTO_WORDS = {"crypto", "bitcoin", "wallet", "ethereum"}

def extract_stage8_features(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL cannot be empty.")
    html, final_url = fetch_webpage(url)
    if html is None:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlsplit(final_url)

    # 1. HasDescription
    description = soup.find(
        "meta",
        attrs={"name": re.compile("^description$", re.I)}
    )
    has_description = int(
        description is not None
        and bool(description.get("content", "").strip())
    )

    # 2. URLTitleMatchScore
    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title else ""
    )
    url_words = set(
        re.findall(
            r"[a-z0-9]+",
            parsed.hostname + parsed.path,
            re.I
        )
    )
    title_words = set(
        re.findall(r"[a-z0-9]+", title.lower())
    )
    match_score = (
        round(
            100 * len(url_words & title_words) / len(url_words),
            2
        )
        if url_words else 0.0
    )

    # 3. Keyword indicators
    page_text = (
        parsed.hostname + " " +
        parsed.path + " " +
        soup.get_text(" ", strip=True)
    ).lower()
    words = set(re.findall(r"[a-z0-9]+", page_text))
    return {
        "HasDescription": has_description,
        "URLTitleMatchScore": match_score,
        "Bank": int(bool(words & BANK_WORDS)),
        "Pay": int(bool(words & PAY_WORDS)),
        "Crypto": int(bool(words & CRYPTO_WORDS))
    }

if __name__ == "__main__":
    test_url = input("Enter URL: ")
    try:
        result = extract_stage8_features(test_url)
        for feature, value in result.items():
            print(f"{feature}: {value}")
        print("Total Stage 8 Features:", len(result))
    except Exception as error:
        print("Stage 8 extraction failed:", error)

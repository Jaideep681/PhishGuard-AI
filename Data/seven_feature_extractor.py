"""
Stage 7: HTML Reference Feature Extraction

Features:
- NoOfSelfRef
- NoOfEmptyRef
- NoOfExternalRef

Uses the secure webpage-fetching function from Stage 5.
"""

from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup
from five_feature_extractor import fetch_webpage

def extract_stage7_features(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL cannot be empty.")
    html, final_url = fetch_webpage(url)
    if html is None:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlsplit(final_url)
    hostname = parsed.hostname.lower()
    self_refs = 0
    empty_refs = 0
    external_refs = 0
    for tag in soup.find_all(
        ["a", "link", "script", "img", "iframe"]
    ):
        reference = tag.get("href") or tag.get("src")
        if reference is None:
            continue
        reference = reference.strip()
        if not reference:
            empty_refs += 1
            continue
        if reference.startswith(
            ("#", "javascript:", "mailto:", "tel:", "data:")
        ):
            continue
        target = urlsplit(urljoin(final_url, reference))
        if not target.hostname:
            self_refs += 1
        elif target.hostname.lower() == hostname:
            self_refs += 1
        else:
            external_refs += 1
    return {
        "NoOfSelfRef": self_refs,
        "NoOfEmptyRef": empty_refs,
        "NoOfExternalRef": external_refs
    }

if __name__ == "__main__":
    test_url = input("Enter URL: ")
    try:
        result = extract_stage7_features(test_url)
        for feature, value in result.items():
            print(f"{feature}: {value}")
        print("Total Stage 7 Features:", len(result))
    except Exception as error:
        print("Stage 7 extraction failed:", error)


"""
Stage 3: Additional URL Feature Extraction (11+7+7=25 features)
Imports the 18 features from two_feature_extractor.py
and adds additional URL-structure features.
Reference-data and webpage-dependent features are
intentionally not fabricated in this stage.
"""

from urllib.parse import urlsplit
from two_feature_extractor import extract_stage_two_features

def extract_stage_three_features(url):

    #Extract Stage 1 + Stage 2 + Stage 3 features.
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")
    url = url.strip()

    # Get all 18 features from Stage 1 and Stage 2
    features = extract_stage_two_features(url)
    parsed = urlsplit(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    # Stage 3: Additional URL-structure features

    # 1. PathLength
    path_length = len(path)

    # 2. QueryLength
    query_length = len(query)

    # 3. NoOfDotsInURL
    dot_count = url.count(".")

    # 4. NoOfHyphensInURL
    hyphen_count = url.count("-")

    # 5. NoOfUnderscoresInURL
    underscore_count = url.count("_")

    # 6. NoOfSlashesInURL
    slash_count = url.count("/")

    # 7. NoOfQueryParameters
    query_parameter_count = (len([item for item in query.split("&") if item]) if query else 0)
    features.update({
        "PathLength": path_length,
        "QueryLength": query_length,
        "NoOfDotsInURL": dot_count,
        "NoOfHyphensInURL": hyphen_count,
        "NoOfUnderscoresInURL": underscore_count,
        "NoOfSlashesInURL": slash_count,
        "NoOfQueryParameters": query_parameter_count
    })
    return features

if __name__ == "__main__":
    test_url = input("Enter URL to extract features: ")
    try:
        result = extract_stage_three_features(test_url)
        print("\nPHISHGUARD AI - STAGE 3 FEATURE EXTRACTION")
        print("-" * 55)
        for feature_name, feature_value in result.items():
            print(f"{feature_name}: {feature_value}")
        print("-" * 55)
        print("Total extracted features:", len(result))
    except (ValueError, KeyError) as error:
        print("Feature extraction error:", error)


"""
Stage 2: Additional URL Feature Extraction
Imports the 11 features from one_feature_extractor.py
and adds 7 additional URL features. Total=11+7=18
Note:
Some definitions are provisional and must be validated
against the original PhiUSIIL feature-generation methodology
before using them with the trained model.
"""

import re
import string
from one_feature_extractor import extract_url_features
def extract_stage_two_features(url):
    #Extract the 18 combined URL features: 11 from Stage 1 + 7 from Stage 2.

    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")
    url = url.strip()

    # Stage 1: Extract the first 11 features
    features = extract_url_features(url)

    # Stage 2: Additional feature calculations
    url_length = features["URLLength"]
    letter_count = features["NoOfLettersInURL"]
    digit_count = features["NoOfDegitsInURL"]

    # 1. LetterRatioInURL
    letter_ratio = (letter_count/url_length if url_length else 0)

    # 2. DegitRatioInURL
    digit_ratio = (digit_count/url_length if url_length else 0)

    ''' 3. Count percent-encoded character sequences
    Example: %20, %2F, %3D '''
    encoded_sequences = re.findall(r"%[0-9a-fA-F]{2}", url)

    ''' 4. Count @ symbols and percent-encoded sequences
    This is a provisional obfuscation heuristic. '''
    obfuscated_count = (len(encoded_sequences)+url.count("@"))

    # 5. HasObfuscation
    has_obfuscation = int(obfuscated_count>0)

    # 6. ObfuscationRatio
    obfuscation_ratio = (obfuscated_count/url_length if url_length else 0)

    ''' 7. NoOfOtherSpecialCharsInURL
    Provisional definition: Count punctuation except ?, = and &. '''
    excluded_chars = set("?=&")
    other_special_chars = sum(
        1
        for char in url
        if char in string.punctuation
        and char not in excluded_chars
    )

    # Add Stage 2 features
    features.update({
        "LetterRatioInURL": letter_ratio,
        "DegitRatioInURL": digit_ratio,
        "HasObfuscation": has_obfuscation,
        "NoOfObfuscatedChar": obfuscated_count,
        "ObfuscationRatio": obfuscation_ratio,
        "NoOfOtherSpecialCharsInURL": other_special_chars,
        "SpacialCharRatioInURL": (other_special_chars / url_length if url_length else 0
        )
    })
    return features

if __name__ == "__main__":
    test_url = input("Enter URL to extract features: ")
    try:
        result = extract_stage_two_features(test_url)
        print("\nPHISHGUARD AI - STAGE 2 FEATURE EXTRACTION")
        print("-" * 50)
        for feature_name, feature_value in result.items():
            print(f"{feature_name}: {feature_value}")
        print("-" * 50)
        print("Total extracted features:", len(result))
    except (ValueError, KeyError) as error:
        print("Feature extraction error:", error)

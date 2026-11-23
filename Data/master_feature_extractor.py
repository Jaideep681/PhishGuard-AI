
"""
PHISHGUARD AI
MASTER FEATURE EXTRACTOR
Combines feature extraction from Stages 1–8.
Features:
- URL-based features
- Reference-data features
- Webpage-based features
- Redirect analysis
- HTML reference analysis
- Additional webpage analysis
IMPORTANT:
- Stage 3 includes the features from Stages 1 and 2.
- Stage 4 includes Stage 3 features when reference_data is supplied.
- Stage 5–8 add their respective independent features.
- Validate all feature formulas against the original
  PhiUSIIL methodology before model integration.
"""

from three_feature_extractor import extract_stage_three_features
from four_feature_extractor import extract_stage_four_features
from five_feature_extractor import extract_webpage_features
from six_feature_extractor import extract_stage6_features
from seven_feature_extractor import extract_stage7_features
from eight_feature_extractor import extract_stage8_features
from reference_data_extractor import ReferenceDataExtractor

# Original 50 PhiUSIIL model feature names
ORIGINAL_FEATURES = {
    "URLLength", "DomainLength", "IsDomainIP",
    "URLSimilarityIndex", "CharContinuationRate",
    "TLDLegitimateProb", "URLCharProb", "TLDLength",
    "NoOfSubDomain", "HasObfuscation", "NoOfObfuscatedChar",
    "ObfuscationRatio", "NoOfLettersInURL", "LetterRatioInURL",
    "NoOfDegitsInURL", "DegitRatioInURL", "NoOfEqualsInURL",
    "NoOfQMarkInURL", "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL", "SpacialCharRatioInURL",
    "IsHTTPS", "LineOfCode", "LargestLineLength", "HasTitle",
    "DomainTitleMatchScore", "URLTitleMatchScore", "HasFavicon",
    "Robots", "IsResponsive", "NoOfURLRedirect",
    "NoOfSelfRedirect", "HasDescription", "NoOfPopup",
    "NoOfiFrame", "HasExternalFormSubmit", "HasSocialNet",
    "HasSubmitButton", "HasHiddenFields", "HasPasswordField",
    "Bank", "Pay", "Crypto", "HasCopyrightInfo", "NoOfImage",
    "NoOfCSS", "NoOfJS", "NoOfSelfRef", "NoOfEmptyRef",
    "NoOfExternalRef"
}

#Initializing the reference extractor
LEGITIMATE_LABEL = 1
reference_extractor = ReferenceDataExtractor(
    legitimate_label=LEGITIMATE_LABEL
)

def extract_all_features(url, reference_data=None):
    all_features = {}
    def add_features(new_features, stage_name):
        duplicates = set(all_features) & set(new_features)
        if duplicates:
            raise ValueError(
                f"Duplicate features in {stage_name}: {duplicates}"
            )
        all_features.update(new_features)

    # Stages 1, 2 and 3
    add_features(
        extract_stage_three_features(url), "Stage 3"
    )

    # Stage 4 requires reference data
    if reference_data is not None:
        add_features(
            extract_stage_four_features(url, reference_data), "Stage 4"
        )

    # Stage 5: Webpage features
    add_features(
        extract_webpage_features(url), "Stage 5"
    )

    # Stage 6: URL and redirect features
    add_features(
        extract_stage6_features(url), "Stage 6"
    )

    # Stage 7: HTML reference features
    add_features(
        extract_stage7_features(url), "Stage 7"
    )

    # Stage 8: Additional webpage features
    add_features(
        extract_stage8_features(url), "Stage 8"
    )
    return all_features

def audit_features(features):
    available = set(features)
    missing = ORIGINAL_FEATURES - available
    extra = available - ORIGINAL_FEATURES
    print("\n" + "=" * 50)
    print("PHISHGUARD AI - MASTER FEATURE AUDIT")
    print("=" * 50)
    print("Total extracted features:", len(features))
    print("Original features found:", len(ORIGINAL_FEATURES & available))
    print("Original features missing:", len(missing))
    print("Additional custom features:", len(extra))

    if missing:
        print("\nMISSING ORIGINAL FEATURES:")
        for feature in sorted(missing):
            print("-", feature)
    else:
        print("\nAll original feature names are present.")

    if extra:
        print("\nADDITIONAL CUSTOM FEATURES:")
        for feature in sorted(extra):
            print("-", feature)
    else:
        print("There is no extra/additional features.")
    print("-" * 50)

# Testing
if __name__ == "__main__":
    test_url = input("Enter URL: ").strip()
    # Extract reference-dependent features from MySQL
    reference_data = reference_extractor.extract(test_url)

    # Extract all features
    features = extract_all_features(
        test_url,
        reference_data=reference_data
    )
    print("\nPHISHGUARD AI - MASTER FEATURE EXTRACTION")
    print("=" * 50)
    for name, value in features.items():
        print(f"{name}: {value}")
    print("\nTotal extracted features:", len(features))

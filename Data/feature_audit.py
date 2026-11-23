
"""
PhishGuard AI
Feature Audit: Compare extracted features with the
original 50 numeric PhiUSIIL model features.

This is a name-based audit. It does not validate
whether the extraction formulas are identical to
the original dataset methodology.
"""

# 1. Original 50 numeric features used by the model
ORIGINAL_50_FEATURES = {
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "URLSimilarityIndex",
    "CharContinuationRate",
    "TLDLegitimateProb",
    "URLCharProb",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "LineOfCode",
    "LargestLineLength",
    "HasTitle",
    "DomainTitleMatchScore",
    "URLTitleMatchScore",
    "HasFavicon",
    "Robots",
    "IsResponsive",
    "NoOfURLRedirect",
    "NoOfSelfRedirect",
    "HasDescription",
    "NoOfPopup",
    "NoOfiFrame",
    "HasExternalFormSubmit",
    "HasSocialNet",
    "HasSubmitButton",
    "HasHiddenFields",
    "HasPasswordField",
    "Bank",
    "Pay",
    "Crypto",
    "HasCopyrightInfo",
    "NoOfImage",
    "NoOfCSS",
    "NoOfJS",
    "NoOfSelfRef",
    "NoOfEmptyRef",
    "NoOfExternalRef"
}

# 2. Features currently represented in each stage
STAGE_1_FEATURES = {
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "TLDLength",
    "NoOfSubDomain",
    "NoOfLettersInURL",
    "NoOfDegitsInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "IsHTTPS"
}
STAGE_2_FEATURES = {
    "LetterRatioInURL",
    "DegitRatioInURL",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL"
}

# These are custom features, not original PhiUSIIL columns.
STAGE_3_CUSTOM_FEATURES = {
    "PathLength",
    "QueryLength",
    "NoOfDotsInURL",
    "NoOfHyphensInURL",
    "NoOfUnderscoresInURL",
    "NoOfSlashesInURL",
    "NoOfQueryParameters"
}
STAGE_4_FEATURES = {
    "URLSimilarityIndex",
    "TLDLegitimateProb",
    "URLCharProb"
}
STAGE_5_FEATURES = {
    "LineOfCode",
    "LargestLineLength",
    "HasTitle",
    "DomainTitleMatchScore",
    "HasFavicon",
    "Robots",
    "IsResponsive",
    "NoOfPopup",
    "NoOfiFrame",
    "HasExternalFormSubmit",
    "HasSocialNet",
    "HasSubmitButton",
    "HasHiddenFields",
    "HasPasswordField",
    "HasCopyrightInfo",
    "NoOfImage",
    "NoOfCSS",
    "NoOfJS"
}

STAGE_6_FEATURES = {
    "CharContinuationRate",
    "NoOfURLRedirect",
    "NoOfSelfRedirect"
}

STAGE_7_FEATURES = {
    "NoOfSelfRef",
    "NoOfEmptyRef",
    "NoOfExternalRef"
}

STAGE_8_FEATURES = {
    "HasDescription",
    "URLTitleMatchScore",
    "Bank",
    "Pay",
    "Crypto"
}

# 3. Combine all current stage features
CURRENT_ORIGINAL_CANDIDATES = (
    STAGE_1_FEATURES
    | STAGE_2_FEATURES
    | STAGE_4_FEATURES
    | STAGE_5_FEATURES
    | STAGE_6_FEATURES
    | STAGE_7_FEATURES
    | STAGE_8_FEATURES
)

ALL_CURRENT_FEATURES = (
    CURRENT_ORIGINAL_CANDIDATES | STAGE_3_CUSTOM_FEATURES
)

# 4. Compare feature names
IMPLEMENTED_ORIGINAL = (
    ORIGINAL_50_FEATURES & CURRENT_ORIGINAL_CANDIDATES
)
MISSING_FEATURES = (
    ORIGINAL_50_FEATURES - CURRENT_ORIGINAL_CANDIDATES
)
EXTRA_CUSTOM_FEATURES = (
    ALL_CURRENT_FEATURES - ORIGINAL_50_FEATURES
)

# 5. Display audit report
print("\n" + "=" * 60)
print("       PHISHGUARD AI - FEATURE AUDIT REPORT")
print("=" * 60)
print("\nOriginal model features:", len(ORIGINAL_50_FEATURES))
print("Original features represented:", len(IMPLEMENTED_ORIGINAL))
print("Original features missing:", len(MISSING_FEATURES))
print("Additional custom features:", len(EXTRA_CUSTOM_FEATURES))
print("\n" + "-" * 60)
print("              MISSING ORIGINAL FEATURES")
print("-" * 60)
for number, feature in enumerate(sorted(MISSING_FEATURES), start=1):
    print(f"{number}. {feature}")
print("\n" + "-" * 60)
print("              ADDITIONAL CUSTOM FEATURES")
print("-" * 60)
for number, feature in enumerate(sorted(EXTRA_CUSTOM_FEATURES), start=1):
    print(f"{number}. {feature}")
print("\n" + "-" * 60)
print("              ORIGINAL FEATURES REPRESENTED")
print("-" * 60)
for number, feature in enumerate(sorted(IMPLEMENTED_ORIGINAL), start=1):
    print(f"{number}. {feature}")
if not MISSING_FEATURES:
    print("All original feature names are represented.")
else:
    print("\nFeature extraction is not yet complete.")

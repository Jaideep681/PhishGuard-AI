
"""
Stage 4: Reference-Data-Dependent Feature Extraction (11+7+7+3)
Adds only 3 reference-dependent features:
1. URLSimilarityIndex
2. TLDLegitimateProb
3. URLCharProb
Stage 4 does not re-extract previous stage features.
IMPORTANT:
The reference values and similarity calculation must
come from the original PhiUSIIL methodology.
This module does not generate fake/default probabilities.
"""

def extract_stage_four_features(url, reference_data):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")
    if not isinstance(reference_data, dict):
        raise TypeError("Reference_data must be a dictionary.")
    required_fields = [
        "URLSimilarityIndex",
        "TLDLegitimateProb",
        "URLCharProb"
    ]
    missing_fields = [
        field for field in required_fields
        if field not in reference_data
    ]
    if missing_fields:
        raise ValueError(
            "Missing reference values: " + ", ".join(missing_fields)
        )
    # Validate reference values
    for field in required_fields:
        value = reference_data[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{field} must be numeric.")
        if not 0 <= value <= 100:
            raise ValueError(f"{field} must be between 0 and 100.")
    # Return ONLY the three reference-dependent features
    features = {
        "URLSimilarityIndex": reference_data["URLSimilarityIndex"],
        "TLDLegitimateProb": reference_data["TLDLegitimateProb"],
        "URLCharProb": reference_data["URLCharProb"]
    }
    return features

if __name__ == "__main__":
    test_url = input("Enter URL to extract features: ").strip()
    demo_reference_data = {
        "URLSimilarityIndex": 0.0,
        "TLDLegitimateProb": 0.0,
        "URLCharProb": 0.0
    }
    try:
        result = extract_stage_four_features(
            test_url,
            demo_reference_data
        )
        print("\nPHISHGUARD AI - STAGE 4 FEATURE EXTRACTION")
        print("-" * 55)
        for feature_name, feature_value in result.items():
            print(f"{feature_name}: {feature_value}")
        print("-" * 55)
        print("Total extracted features:", len(result))
        print("NOTE: Demo values are placeholders, not model-ready.")
    except (ValueError, TypeError, KeyError) as error:
        print("Feature extraction error:", error)

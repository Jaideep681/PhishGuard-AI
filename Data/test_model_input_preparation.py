import joblib
import pandas as pd
from master_feature_extractor import extract_all_features
from reference_data_extractor import ReferenceDataExtractor
from model_input_preparation import ModelInputPreparation
MODEL_PATH = (
    r"C:\Users\Jaideep\Desktop\YMCA COLLEGE BCA\MINOR PROJECT\PhishGuard AI\Phish_Trained_Model\phishing_model.pkl"
)
TEST_URL = "https://example.com"

def print_section(title, dataframe):
    print("\n" + "=" * 75)
    print(f" {title}")
    print("=" * 75)
    if dataframe.empty:
        print("No features available.")
        return
    print(
        dataframe.to_string(
            index=False,
            justify="left",
            max_colwidth=35
        )
    )

def main():
    print("\n" + "#" * 75)
    print("             PHISHGUARD AI - MODEL INPUT PREPARATION TEST")
    print("#" * 75)
    print(f"\nURL being tested: {TEST_URL}")

    # 1. Load trained model
    print("\n[1/5] Loading trained model...")
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")

    # 2. Extract reference data
    print("\n[2/5] Extracting reference data...")
    reference_extractor = ReferenceDataExtractor(
        legitimate_label=0
    )
    reference_data = reference_extractor.extract(TEST_URL)
    print("Reference data extracted successfully.")

    # 3. Extract all features
    print("\n[3/5] Extracting URL and webpage features...")
    extracted_features = extract_all_features(
        TEST_URL,
        reference_data=reference_data
    )
    expected_columns = list(model.feature_names_in_)
    extra_features = [
        feature for feature in extracted_features
        if feature not in expected_columns
    ]
    print("\nEXTRA FEATURES NOT USED BY MODEL:")
    print("-" * 50)
    for number, feature in enumerate(extra_features, start=1):
        print(f"{number}. {feature}: {extracted_features[feature]}")
    print("-" * 50)
    print(f"Total extracted features: {len(extracted_features)}")

    # 4. Prepare model input
    print("\n[4/5] Preparing model input...")
    preparer = ModelInputPreparation(model)
    model_input = preparer.prepare_input(
        TEST_URL,
        extracted_features
    )
    print("Model input prepared successfully.")

    # 5. Display organised output
    print("\n[5/5] Displaying prepared features...")
    print("\n" + "#" * 75)
    print("                  \tMODEL INPUT SUMMARY")
    print("#" * 75)
    print(f"\nURL              : {TEST_URL}")
    print(f"Total columns    : {model_input.shape[1]}")
    print(f"Total records    : {model_input.shape[0]}")

    # Separate numeric and metadata columns
    numeric_columns = model_input.select_dtypes(
        include=["number"]
    ).columns.tolist()
    metadata_columns = [
        column for column in model_input.columns
        if column not in numeric_columns
    ]

    # Display metadata
    metadata_df = pd.DataFrame({
        "Feature": metadata_columns,
        "Value": [
            str(model_input.iloc[0][column])
            for column in metadata_columns
        ]
    })
    print_section("A. URL AND PAGE METADATA", metadata_df)

    # Display numeric features in groups of 10
    numeric_df = model_input[numeric_columns].T.reset_index()
    numeric_df.columns = ["Feature", "Value"]
    for start in range(0, len(numeric_df), 10):
        end = min(start + 10, len(numeric_df))
        group_number = (start // 10) + 1
        print_section(
            f"B. NUMERIC FEATURES - GROUP {group_number}",
            numeric_df.iloc[start:end]
        )

    # Final validation
    print("\n" + "#" * 75)
    print("                    \tFINAL VALIDATION")
    print("#" * 75)
    print(f"Expected columns : {len(preparer.expected_columns)}")
    print(f"Actual columns   : {model_input.shape[1]}")
    print(f"Numeric features : {len(numeric_columns)}")
    print(f"Metadata fields  : {len(metadata_columns)}")
    if list(model_input.columns) == preparer.expected_columns:
        print("\nSUCCESS: Column order matches the trained model.")
    else:
        print("\nERROR: Column order does not match the trained model.")
    print("\n" + "#" * 75)
    print("                  \tTEST COMPLETED")
    print("#" * 75)

#Print all the outcomes
if __name__ == "__main__":
    main()

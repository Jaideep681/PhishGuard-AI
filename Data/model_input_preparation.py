import os
import pandas as pd
from urllib.parse import urlsplit

class ModelInputPreparation:
    """Prepares extracted URL and webpage features in the exact
    column order expected by the trained Scikit-learn pipeline."""

    def __init__(self, model):
        if model is None:
            raise ValueError("A trained model must be provided.")
        self.model = model

        # Read the exact input columns saved in the trained pipeline.
        if not hasattr(model, "feature_names_in_"):
            raise ValueError(
                "The model does not contain feature_names_in_. "
                "Check that the trained pipeline was saved correctly."
            )
        self.expected_columns = list(model.feature_names_in_)
        if len(self.expected_columns) != 55:
            raise ValueError(
                f"Expected 55 model input columns, "
                f"but the model expects {len(self.expected_columns)}."
            )

    @staticmethod
    def extract_url_metadata(url):
        """Extracts the non-numeric metadata fields required by the model."""

        parsed_url = urlsplit(url)
        hostname = parsed_url.hostname or ""
        domain = hostname
        tld = ""
        if hostname:
            parts = hostname.split(".")
            if len(parts) >= 2:
                tld = parts[-1]
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "index"
        return {
            "FILENAME": filename,
            "URL": url,
            "Domain": domain,
            "TLD": tld
        }

    def prepare_input(self, url, extracted_features):
        """Combines URL metadata and extracted features, then creates
        a DataFrame with the exact 55 columns expected by the model.
        Parameters:
            url: The URL being scanned.
            extracted_features: Dictionary returned by the master feature extractor.
        Returns:
            pandas DataFrame containing exactly 55 columns.
        """

        if not isinstance(url, str) or not url.strip():
            raise ValueError("A valid URL string is required.")

        if not isinstance(extracted_features, dict):
            raise TypeError("extracted_features must be a dictionary.")

        # Copy the original dictionary to avoid modifying it.
        features = extracted_features.copy()

        # Add metadata fields derived from the URL.
        metadata = self.extract_url_metadata(url)

        for key, value in metadata.items():
            features.setdefault(key, value)

        # Title is text metadata. An empty string is used if the webpage extractor could not obtain a title.
        features.setdefault("Title", "")

        # Identify missing columns.
        missing_columns = [
            column for column in self.expected_columns
            if column not in features
        ]

        if missing_columns:
            raise ValueError(
                "Required model features are missing:\n" + "\n".join(missing_columns)
            )

        # Keep only the exact columns expected by the model.
        # This excludes additional custom features.
        model_data = {
            column: features[column] for column in self.expected_columns
        }

        # Create DataFrame in the model's original column order.
        input_df = pd.DataFrame(
            [model_data], columns=self.expected_columns
        )

        # Reject missing values rather than guessing replacements.
        null_columns = input_df.columns[
            input_df.isnull().any()
        ].tolist()

        if null_columns:
            raise ValueError(
                "The following model features contain missing values:\n" + "\n".join(null_columns)
            )

        # Validate the 50 numeric features.
        numeric_columns = input_df.select_dtypes(
            include=["number"]
        ).columns.tolist()
        if len(numeric_columns)!= 50:
            raise ValueError(
                f"The model input should contain 50 numeric features, but received {len(numeric_columns)}."
            )

        # Ensure the numeric values are finite.
        numeric_values = input_df[numeric_columns]
        if not numeric_values.map(
            lambda value: pd.notna(value) and float("-inf") < float(value) < float("inf")).all().all():
            raise ValueError(
                "One or more numeric features contain invalid values."
            )

        # Final structure check
        if list(input_df.columns)!=self.expected_columns:
            raise ValueError(
                "The prepared DataFrame column order does not match the trained model."
            )
        return input_df

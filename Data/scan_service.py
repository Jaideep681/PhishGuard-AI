"""
PHISHGUARD AI - SCAN SERVICE
Connects the existing reference-data extractor, master feature extractor,
and trained prediction pipeline into one URL-scanning workflow.
This module does not replace or modify the existing extractor/model files.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

class ScanService:
    """Orchestrates feature extraction and machine-learning prediction."""

    def __init__(self, predictor=None, feature_extractor=None,
                 reference_extractor=None):
        # Lazy imports prevent loading the model/database until the service is actually initialized, and allow dependency injection in tests.
        if predictor is None:
            from prediction import PhishGuardPredictor
            predictor = PhishGuardPredictor()
        if feature_extractor is None or reference_extractor is None:
            from master_feature_extractor import (
                extract_all_features,
                reference_extractor as master_reference_extractor,
            )
            if feature_extractor is None:
                feature_extractor = extract_all_features
            if reference_extractor is None:
                reference_extractor = master_reference_extractor
        self.predictor = predictor
        self.feature_extractor = feature_extractor
        self.reference_extractor = reference_extractor
        ''' These are the five non-numeric metadata fields in the trained pipeline's 55-column input. The preprocessing pipeline is expected
         to pass them through its metadata branch and exclude them from the Random Forest's 50 numeric inputs.'''
        self.metadata_fields = {"FILENAME", "URL", "Domain", "TLD", "Title"}

    @staticmethod
    def validate_url(url: str) -> str:
        """Perform basic input validation; network safety remains the responsibility of the individual extractors and deployment layer."""
        if not isinstance(url, str):
            raise TypeError("URL must be provided as text.")
        url = url.strip()
        if not url:
            raise ValueError("Please enter a URL.")
        if any(character.isspace() for character in url):
            raise ValueError("URL must not contain whitespace.")
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported.")
        if not parsed.hostname:
            raise ValueError("The URL must contain a valid hostname.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("URLs containing embedded credentials are not allowed.")
        # Accessing .port also validates malformed port strings.
        try:
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("The URL contains an invalid port.") from exc

        return url

    @staticmethod
    def _metadata_for_url(url: str, extracted_features: dict[str, Any]) -> dict:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
        ''' Match the five metadata column names expected by the trained model.
        The original dataset's FILENAME convention should be checked before interpreting this metadata field;
        it is passed through the pipeline.'''
        filename = Path(parsed.path).name or "index"
        return {
            "FILENAME": filename,
            "URL": url,
            "Domain": hostname,
            "TLD": hostname.rsplit(".", 1)[-1] if "." in hostname else "",
            "Title": extracted_features.get("Title", ""),
        }

    def scan_url(self, url: str) -> dict:
        """Extract features, prepare model fields, and return a prediction.
        Extraction/network/database/model errors are raised to the caller.
        They must not be converted into a phishing verdict."""
        clean_url = self.validate_url(url)

        # Stage 4 reference features are sourced from the existing MySQL reference-data extractor instantiated by master_feature_extractor.
        reference_data = self.reference_extractor.extract(clean_url)
        extracted_features = self.feature_extractor(
            clean_url,
            reference_data=reference_data,
        )
        if not isinstance(extracted_features, dict):
            raise TypeError("The master feature extractor must return a dictionary.")
        model_features = dict(extracted_features)
        model_features.update(self._metadata_for_url(clean_url, extracted_features))
        expected = list(self.predictor.expected_features)
        missing = [name for name in expected if name not in model_features]
        if missing:
            raise ValueError(
                "Feature extraction did not produce all model inputs. "
                f"Missing {len(missing)} fields: {missing}"
            )

        ''' Remove custom Stage 3 fields and any other extras from the model
        payload. prediction.py itself creates the DataFrame in the exact
        training-time column order.'''
        ordered_model_features = {
            name: model_features[name] for name in expected
        }
        prediction = self.predictor.predict(ordered_model_features)
        predicted_class = prediction["predicted_class"]
        probabilities = prediction.get("class_probabilities") or {}
        predicted_probability = probabilities.get(str(predicted_class))
        return {
            "status": "completed",
            "scanned_url": clean_url,
            "predicted_class": predicted_class,
            "confidence_score": (
                float(predicted_probability) if predicted_probability is not None else None
            ),
            "class_probabilities": probabilities,
            "extracted_feature_count": len(extracted_features),
            "model_input_feature_count": len(expected),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "message": (
                "Prediction completed. Map the numeric class to "
                "Legitimate/Phishing only after confirming the dataset labels."
            ),
        }

# Convenience function for simple use from Flask routes or other modules.
_default_service = None
def scan_url(url: str) -> dict:
    global _default_service
    if _default_service is None:
        _default_service = ScanService()
    return _default_service.scan_url(url)

if __name__ == "__main__":
    print("PHISHGUARD AI - SCAN SERVICE TEST")
    print("-" * 45)
    entered_url = input("Enter a URL to scan: ").strip()
    try:
        result = scan_url(entered_url)
        for key, value in result.items():
            print(f"{key}: {value}")
    except Exception as error:
        print("\nScan could not be completed.")
        print(f"Reason: {error}")
        print("No phishing/legitimate verdict was generated.")

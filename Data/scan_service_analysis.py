"""
PHISHGUARD AI - SCAN SERVICE + SCAN HISTORY INTEGRATION
Uses the existing:
  - prediction.py
  - master_feature_extractor.py
  - scan_analysis.py
No existing database table or extractor is recreated here.
Important 'scan_analysis.py':
  * scan_analysis.save_scan() expects confidence_score in the range 0..100.
  * This service converts model probabilities (0..1) to percentages.
  * Until the dataset label mapping is confirmed, results are stored as Class_<number>, not incorrectly labelled Legitimate or Phishing.
  * Supply user_id from a VERIFIED Firebase ID token on the backend. Never accept a browser-provided user_id as trusted identity.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

class ScanService:

    """Coordinates URL analysis, model prediction, and optional history save."""
    def __init__(
        self,predictor=None,
        feature_extractor=None,
        reference_extractor=None,
        history_manager=None,
        class_labels: Optional[dict[int, str]] = None,
    ):
        # Lazy imports make the module easier to import in Flask and tests.
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
        if history_manager is None:
            import scan_analysis as history_manager
        self.predictor = predictor
        self.feature_extractor = feature_extractor
        self.reference_extractor = reference_extractor
        self.history = history_manager

        """ Example only: {0: "Legitimate", 1: "Phishing"}.
        Keep unset until the dataset's actual label mapping is verified."""
        self.class_labels = class_labels or {           #I make changes here...
            1: "Phishing",
            0: "Legitimate"
        }

    @staticmethod
    def validate_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("URL must be provided as text.")
        url = url.strip()
        if not url:
            raise ValueError("Please enter a URL.")
        if any(ch.isspace() for ch in url):
            raise ValueError("URL must not contain whitespace.")
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported.")
        if not parsed.hostname:
            raise ValueError("The URL must contain a hostname.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("URLs containing embedded credentials are not allowed.")
        try:
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("The URL contains an invalid port.") from exc
        return url

    @staticmethod
    def _metadata_for_url(url: str, extracted: dict[str, Any]) -> dict:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
        return {
            "FILENAME": Path(parsed.path).name or "index",
            "URL": url,
            "Domain": hostname,
            "TLD": hostname.rsplit(".", 1)[-1] if "." in hostname else "",
            "Title": extracted.get("Title", ""),
        }

    def _predict(self, clean_url: str) -> tuple[dict, dict]:
        reference_data = self.reference_extractor.extract(clean_url)
        extracted = self.feature_extractor(
            clean_url,
            reference_data=reference_data,
        )
        if not isinstance(extracted, dict):
            raise TypeError("Master feature extractor must return a dictionary.")
        combined = dict(extracted)
        combined.update(self._metadata_for_url(clean_url, extracted))
        expected = list(self.predictor.expected_features)
        missing = [name for name in expected if name not in combined]
        if missing:
            raise ValueError(
                f"Missing {len(missing)} model input fields: {missing}"
            )
        ordered = {name: combined[name] for name in expected}
        prediction = self.predictor.predict(ordered)
        return extracted, prediction

    def scan_url(
        self,url: str,
        user_id: Optional[str] = None,
        save_history: bool = True,
    ) -> dict:
        """
        Run one scan and optionally save it.
        If save_history=True but user_id is absent, prediction still completes;
        history is not saved. In the authenticated Flask API, pass the Firebase UID obtained from a verified ID token.
        """
        clean_url = self.validate_url(url)
        extracted, prediction = self._predict(clean_url)
        predicted_class = int(prediction["predicted_class"])
        probabilities = prediction.get("class_probabilities") or {}
        probability = probabilities.get(str(predicted_class))
        confidence_percent = (
            round(float(probability) * 100, 2) if probability is not None else None
        )
        display_label = self.class_labels.get(
            predicted_class, f"Class_{predicted_class}"
        )
        result = {
            "status": "completed",
            "scanned_url": clean_url,
            "predicted_class": predicted_class,
            "predicted_label": display_label,
            "confidence_score": confidence_percent,
            "class_probabilities": probabilities,
            "extracted_feature_count": len(extracted),
            "model_input_feature_count": len(self.predictor.expected_features),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "history_saved": False,
            "scan_id": None,
            "message": (
                "Prediction completed successfully. Class labels must be verified against the dataset before treating them as Legitimate or Phishing."
                if predicted_class not in self.class_labels
                else "Prediction completed."
            ),
        }
        if save_history and user_id:
            """ scan_analysis confidence_score is defined as 0..100.
            Keep the complete prediction payload in JSON analysis_details."""
            scan_id = self.history.save_scan(
                user_id=user_id,
                scanned_url=clean_url,
                scan_result=display_label,
                confidence_score=confidence_percent,
                analysis_details={
                    "predicted_class": predicted_class,
                    "predicted_label": display_label,
                    "class_probabilities": probabilities,
                    "extracted_feature_count": len(extracted),
                    "model_input_feature_count": len(self.predictor.expected_features),
                    "scan_timestamp": result["scan_timestamp"],
                },
            )
            result["history_saved"] = True
            result["scan_id"] = scan_id
        elif save_history:
            result["history_message"] = (
                "Not saved: authenticated user_id was not supplied."
            )

        return result

    # User-scoped history operations. Pass only the UID from verified auth.
    def get_history(self, user_id: str, limit: int = 50, offset: int = 0):
        return self.history.get_user_scan_history(user_id, limit, offset)

    def get_scan(self, user_id: str, scan_id: int):
        return self.history.get_scan_by_id(user_id, scan_id)

    def delete_history_item(self, user_id: str, scan_id: int) -> bool:
        return self.history.delete_scan(user_id, scan_id)

    def get_statistics(self, user_id: str) -> dict:
        return self.history.get_scan_statistics(user_id)


# Process-level singleton initialization
_default_service = None
def get_scan_service() -> ScanService:
    """Return a process-level singleton for Flask app use."""
    global _default_service
    if _default_service is None:
        _default_service = ScanService()
    return _default_service
def scan_url(url: str, user_id: Optional[str] = None, save_history: bool = True) -> dict:
    return get_scan_service().scan_url(url, user_id, save_history)

# Single, clean testing execution guard block
if __name__ == "__main__":
    print("PHISHGUARD AI - INTEGRATED SCAN + HISTORY")
    print("-" * 55)
    print("Enter a URL to scan. History saving requires an authenticated user ID.")
    entered_url = input("URL: ").strip()
    entered_user_id = input("Verified user ID (leave blank to skip history): ").strip()
    try:
        service = get_scan_service()
        result = service.scan_url(
            entered_url,
            user_id=entered_user_id or None,
            save_history=True,
        )
        print("\n---- SCAN RESULTS ----")
        for key, value in result.items():
            print(f"{key}: {value}")
    except Exception as exc:
        print("\nScan could not be completed.")
        print(f"Reason: {exc}")
        print("No phishing/legitimate verdict or history record was generated.")

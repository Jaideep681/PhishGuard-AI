import joblib
import pandas as pd
from pathlib import Path

# Load python pickle file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "Phish_Trained_Model" / "phishing_model.pkl"
class PhishGuardPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.expected_features = list(
            self.model.feature_names_in_
        )
        print("PhishGuard AI Model loaded successfully.")
        print("Expected features:", len(self.expected_features))

    def predict(self, features):
        missing = [
            name for name in self.expected_features
            if name not in features
        ]
        if missing:
            raise ValueError(
                f"Missing {len(missing)} required features: {missing}"
            )

        # Preserve the exact training-time column order.
        input_data = pd.DataFrame(
            [[features[name] for name in self.expected_features]],
            columns=self.expected_features
        )
        if input_data.isnull().any().any():
            raise ValueError("Input contains missing values.")
        prediction = self.model.predict(input_data)[0]
        result = {
            "predicted_class": int(prediction),
            "class_probabilities": None
        }
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(input_data)[0]
            result["class_probabilities"] = {
                str(label): float(probability)
                for label, probability in zip(
                    self.model.classes_, probabilities
                )
            }
        return result

if __name__ == "__main__":
    predictor = PhishGuardPredictor()
    print("\nExpected model input columns:")
    for number, feature in enumerate(
        predictor.expected_features, start=1
    ):
        print(number, feature)

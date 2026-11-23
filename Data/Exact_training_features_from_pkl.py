import pickle

model_path = r"C:\Users\Jaideep\Desktop\YMCA COLLEGE BCA\MINOR PROJECT\PhishGuard AI\Phish_Trained_Model/phishing_model.pkl"

with open(model_path, "rb") as file:
    model = pickle.load(file)

print("\n===== PHISHGUARD AI MODEL INSPECTION =====")

print("Expected feature count:", model.n_features_in_)

if hasattr(model, "feature_names_in_"):
    print("\nExpected feature names:")
    for index, feature in enumerate(model.feature_names_in_, start=1):
        print(f"{index}. {feature}")
else:
    print("\nFeature names are not stored in this model.")

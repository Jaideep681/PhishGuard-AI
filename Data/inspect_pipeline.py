import pickle

MODEL_PATH = (
    r"C:\Users\Jaideep\Desktop\YMCA COLLEGE BCA\MINOR PROJECT\PhishGuard AI\Phish_Trained_Model/phishing_model.pkl"
)

with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

print("\n===== PHISHGUARD AI PIPELINE INSPECTION =====")

print("\nPipeline steps:")
for name, step in model.named_steps.items():
    print(f"\nStep name: {name}")
    print("Step type:", type(step).__name__)

    if hasattr(step, "n_features_in_"):
        print("Input features:", step.n_features_in_)

    if hasattr(step, "feature_names_in_"):
        print("Input feature names:")
        print(list(step.feature_names_in_))

    if hasattr(step, "transformers_"):
        print("\nSelected columns by transformer:")
        for transformer_name, transformer, columns in step.transformers_:
            print(f"\n{transformer_name}:")
            if isinstance(columns, (list, tuple)):
                print("Feature count:", len(columns))
                print(list(columns))
            else:
                print(columns)

print("\n===== END OF INSPECTION =====")

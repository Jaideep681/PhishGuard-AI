
$wslScript = @'
cd "/mnt/c/Users/Jaideep/Desktop/YMCA COLLEGE BCA/MINOR PROJECT/PhishGuard AI/Flask_App" || exit 1

source venv_linux/bin/activate || exit 1

python - <<'PY'
import joblib
from pathlib import Path

model_path = Path("..") / "Phish_Trained_Model" / "phishing_model.pkl"
model = joblib.load(model_path)

print("\nPHISHGUARD AI - MODEL VALIDATION")
print("=" * 55)

print("Model type:", type(model).__name__)
print("Model classes:", model.classes_)
print("Expected input features:", model.n_features_in_)

print("\nTRAINING-TIME FEATURE ORDER")
for index, name in enumerate(model.feature_names_in_, start=1):
    print(f"{index:02d}. {name}")

print("\nPIPELINE STRUCTURE")
if hasattr(model, "named_steps"):
    for step_name, step in model.named_steps.items():
        print(f"\n{step_name}: {type(step).__name__}")
        if hasattr(step, "transformers_"):
            for name, transformer, columns in step.transformers_:
                print(f"  {name}: {type(transformer).__name__}")
                print(f"  Columns: {columns}")
else:
    print("No named pipeline steps found.")

print("\n" + "=" * 55)
PY
'@

$wslScript | wsl -e bash -s

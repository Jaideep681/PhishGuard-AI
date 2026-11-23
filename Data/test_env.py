import os
from dotenv import load_dotenv
from pathlib import Path

# Get the folder containing test_env.py
BASE_DIR = Path(__file__).resolve().parent

# Load .env from that folder
ENV_PATH = BASE_DIR / "Credentials.env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

print("Environment file exists:", ENV_PATH.exists())
print("Environment file path:", ENV_PATH)

print("\n--- Database Configuration ---")

print("Database User:", os.getenv("DB_USER"))
print("Database Host:", os.getenv("DB_HOST"))
print("Database Port:", os.getenv("DB_PORT"))
print("Database Name:", os.getenv("DB_NAME"))
print("Database Table:", os.getenv("DB_TABLE"))

if os.getenv("DB_PASSWORD"):
    print("Database Password: Loaded successfully!")
else:
    print("Database Password: Missing!")

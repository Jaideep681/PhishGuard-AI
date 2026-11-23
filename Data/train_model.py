import pandas as pd                             # For reading csv dataset file
from sqlalchemy import create_engine            # For engine generation
import urllib.parse                             # For URL encoding special password characters
import pickle
import os
from dotenv import load_dotenv
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
'''
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)
'''
# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "Credentials.env"
load_dotenv(dotenv_path=ENV_PATH)

# MySQL configuration
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = int(os.getenv("DB_PORT", "3306"))
DATABASE = os.getenv("DB_NAME")
TABLE_NAME = os.getenv("DB_TABLE")

# Validate credentials
required_variables = {
    "DB_USER": USER,
    "DB_PASSWORD": PASSWORD,
    "DB_HOST": HOST,
    "DB_NAME": DATABASE,
    "DB_TABLE": TABLE_NAME
}

missing = [
    key for key, value in required_variables.items()
    if not value
]

if missing:
    raise ValueError(
        f"Missing environment variables: {', '.join(missing)}"
    )

safe_password = urllib.parse.quote_plus(PASSWORD)

#MySQL connection establishment
connection_string=f"mysql+mysqlconnector://{USER}:{safe_password}@{HOST}:{PORT}/{DATABASE}"
engine=create_engine(connection_string)

# Test MySQL connection
try:
    with engine.connect() as connection:
        print("MySQL connection successful!")

except Exception as error:
    print("MySQL connection failed:", error)
    engine.dispose()
    raise

#Load dataset from MySQL Database
query=f"SELECT * FROM {TABLE_NAME}"
df=pd.read_sql(query,con=engine)
print(f"🎉Successfully loaded {df.shape[0]} rows & {df.shape[1]} columns for ML Model!!")

#Load x for features & y for target_label (Preparing stage for Machine Learning)
target_label='label'
x=df.drop(columns=[target_label])
y=df[target_label]
print(f"Cleaned array shape for traning data {x.shape[0]} rows & {x.shape[1]} columns for training the ML Model!")

#Split training and testing datasets
x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

#Find all numeric columns involved in the training model
numeric_features=x_train.select_dtypes(include=['number']).columns.tolist()
if not numeric_features:
    raise ValueError("No numeric features found in the dataset!")

print("\n========== MODEL FEATURE LIST ==========")

for index, feature in enumerate(numeric_features, start=1):
    print(f"{index}. {feature}")

print("\nTotal features used:", len(numeric_features))

print("\n========== DATASET INFORMATION ==========")
print("Dataset shape:", df.shape)
print("Numeric columns:", len(numeric_features))
print("Target column:", target_label)

#Preprocessing stage
preprocessor=ColumnTransformer(
    transformers=[
        ('keep_numeric','passthrough',numeric_features)
    ],
    remainder='drop'     #This dynamically deletes all filename,url,domain,etc
)

#Phishing Pipeline Stage
print("Training RandomForestClassifier by using all cores to facilitate parallel processing via n_jobs=-1...")
phishguard_pipeline=Pipeline(
    steps=[
        ('preprocessing',preprocessor),
        ('classifier',RandomForestClassifier(n_estimators=100,n_jobs=-1,random_state=42))
    ]
)

#Training the unified PhishGuard AI Pipeline
phishguard_pipeline.fit(x_train,y_train)
print("Model Training completed successfully!!")

#Making Pickle file Directory of trained ML Model
print("Making Pickle file directory of trained ML Model...")
MODEL_DIR = r"C:\Users\Jaideep\Desktop\YMCA COLLEGE BCA\MINOR PROJECT\PhishGuard AI\Phish_Trained_Model"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

#Saving 'phishing_model.pkl' as pickle to the directory
print("Saving 'phishing_model.pkl' as pickle to the directory...")
PIPELINE_PATH=os.path.join(MODEL_DIR,'phishing_model.pkl')
with open(PIPELINE_PATH,"wb") as file:
    pickle.dump(phishguard_pipeline,file)
print(f"🎉 SUCCESS! Entire Pipeline pickled to:\n{PIPELINE_PATH}")

# Clean up database pipeline resource link
engine.dispose()

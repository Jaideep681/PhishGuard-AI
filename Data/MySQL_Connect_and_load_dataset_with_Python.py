import pandas as pd                             # For reading csv dataset file
from sqlalchemy import create_engine, types     # For engine generation and data typing
import urllib.parse                             # For URL encoding special password characters
import mysql.connector                          # Basic connector instance to check schema containers
import os
from dotenv import load_dotenv
from pathlib import Path

print("Step 0: Initializing configuration schema maps...")
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
CSV_FILE_PATH = r"C:\Users\Jaideep\Desktop\YMCA COLLEGE BCA\MINOR PROJECT\PhishGuard AI\phiusiil+phishing+url+dataset\PhiUSIIL_Phishing_URL_Dataset.csv"

#Initialize the MySQL Connection
print("Step 1: Creation of database in MySQL...")
try:
    init_conn=mysql.connector.connect(host=HOST,port=PORT,user=USER,password=PASSWORD)
    init_cursor=init_conn.cursor()
    init_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    init_cursor.close()
    init_conn.close()
except Exception as init_err:
    print(f"Database creation or connection is unsuccessful {init_err}")

#Parsing DataSet CSV file and also handling syntaxes
df=pd.read_csv(CSV_FILE_PATH)
print(df["label"].value_counts())
df.columns=df.columns.str.strip()
df.columns=df.columns.str.replace('.','_',regex=False)
df.columns=df.columns.str.replace('-','_',regex=False)
'''
data_type_mappings={}
for col in df.columns:
    if df[col].dtype=="object":
        data_type_mappings[col]=types.TEXT()
'''
#MySQL connection establishment
print("Step 2: Connecting to Local MySQL Connection via SqlalChemy...")
connection_string=f"mysql+mysqlconnector://{USER}:{safe_password}@{HOST}:{PORT}/{DATABASE}"
engine=create_engine(connection_string)

#Transform data into MySQL Table inside DataBase
print("Step 3: Transform data into MySQL Table inside DataBase...")
try:
    df.to_sql(
        name=TABLE_NAME,
        con=engine,
        if_exists='append',
        index=False,
        chunksize=5000                               #For handling the large dataset effortlessly by increasing the transmission load size
    #dtype=data_type_mappings
    )
    print(f"🎉Successfully loaded dataset to MySQL Table {TABLE_NAME} inside {DATABASE}")
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns!")

except Exception as e:
    print("❌Unsuccessful!!")
    engine.dispose()
    print(f"Not loaded to MySQL Table {TABLE_NAME}")

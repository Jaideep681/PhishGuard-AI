"""
PhishGuard AI - scan history manager
Production security:
    Pass user_id only from a Firebase UID obtained after the Flask backend
    verifies the Firebase ID token. Never trust a browser-supplied user_id.
"""

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
from sqlalchemy import (
    JSON, Column, DateTime, Float, Integer, MetaData, String, Table, Text,
    case, create_engine, delete, func, insert, select
)
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "Credentials.env")

# MySQL configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "phishing_database")

#Returns ValueError
if not DB_USER or DB_PASSWORD is None:
    raise RuntimeError("DB_USER or DB_PASSWORD is missing from Data/Credentials.env")

#Connection establishment of Python to MySQL
DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
metadata = MetaData()

scanned_url_history = Table(
    "scanned_url_history",
    metadata,
    Column("scan_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(255), nullable=False),
    Column("scanned_url", Text, nullable=False),
    Column("scan_result", String(50), nullable=False),
    Column("confidence_score", Float, nullable=True),
    Column("scan_date", DateTime, nullable=False, server_default=func.current_timestamp()),
    Column("analysis_details", JSON, nullable=True),
    mysql_engine="InnoDB",
)

def create_scan_history_table() -> None:
    """Create the table if it does not already exist."""
    try:
        metadata.create_all(engine, tables=[scanned_url_history], checkfirst=True)
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not create scanned_url_history: {exc}") from exc

def _check_user_id(user_id: str) -> str:
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("A non-empty user_id is required.")
    return user_id.strip()

def save_scan(
    user_id: str,
    scanned_url: str,
    scan_result: str,
    confidence_score: Optional[float] = None,
    analysis_details: Optional[dict[str, Any]] = None,
) -> int:
    """Save a scan and return its new scan_id. Confidence is 0-100 or None."""
    user_id = _check_user_id(user_id)
    if not isinstance(scanned_url, str) or not scanned_url.strip():
        raise ValueError("scanned_url must not be empty.")
    if not isinstance(scan_result, str) or not scan_result.strip():
        raise ValueError("scan_result must not be empty.")
    if confidence_score is not None:
        confidence_score = float(confidence_score)
        if not 0 <= confidence_score <= 100:
            raise ValueError("confidence_score must be between 0 and 100.")
    if analysis_details is not None and not isinstance(analysis_details, dict):
        raise ValueError("analysis_details must be a dictionary or None.")
    try:
        with engine.begin() as conn:
            result = conn.execute(insert(scanned_url_history).values(
                user_id=user_id,
                scanned_url=scanned_url.strip(),
                scan_result=scan_result.strip(),
                confidence_score=confidence_score,
                analysis_details=analysis_details
            ))
            return int(result.inserted_primary_key[0])
    except (SQLAlchemyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"Could not save scan: {exc}") from exc

def get_user_scan_history(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get only this user's scans, newest first."""
    user_id = _check_user_id(user_id)
    if not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit must be from 1 to 500.")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be zero or greater.")
    statement = (
        select(scanned_url_history)
        .where(scanned_url_history.c.user_id == user_id)
        .order_by(scanned_url_history.c.scan_date.desc(), scanned_url_history.c.scan_id.desc())
        .limit(limit).offset(offset)
    )
    try:
        with engine.connect() as conn:
            return [dict(row) for row in conn.execute(statement).mappings().all()]
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not retrieve user history: {exc}") from exc

def get_scan_by_id(user_id: str, scan_id: int) -> Optional[dict]:
    """Get a scan only if it belongs to this user; otherwise return None."""
    user_id = _check_user_id(user_id)
    if not isinstance(scan_id, int) or scan_id <= 0:
        raise ValueError("scan_id must be a positive integer.")
    statement = select(scanned_url_history).where(
        scanned_url_history.c.user_id == user_id,
        scanned_url_history.c.scan_id == scan_id,
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(statement).mappings().first()
            return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not retrieve scan: {exc}") from exc

def delete_scan(user_id: str, scan_id: int) -> bool:
    """Delete a scan only if it belongs to this user."""
    user_id = _check_user_id(user_id)
    if not isinstance(scan_id, int) or scan_id <= 0:
        raise ValueError("scan_id must be a positive integer.")
    stmt = delete(scanned_url_history).where(
        scanned_url_history.c.user_id == user_id,
        scanned_url_history.c.scan_id == scan_id,
    )
    try:
        with engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount > 0
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not delete scan: {exc}") from exc


def get_scan_statistics(user_id: str) -> dict:
    """Get result counts for one user, not all users."""
    user_id = _check_user_id(user_id)
    result_col = scanned_url_history.c.scan_result
    statement = select(
        func.count().label("total_scans"),
        func.sum(
            case((result_col.in_(["Legitimate", "Class_1"]), 1), else_=0)
            ).label("legitimate_scans"),
        func.sum(
            case((result_col.in_(["Phishing", "Class_0"]), 1), else_=0)
        ).label("phishing_scans"),
        func.sum(
            case((result_col == "Suspicious", 1), else_=0)
        ).label("suspicious_scans"),
        func.sum(
            case((result_col == "Error", 1), else_=0)
        ).label("error_scans"),
    ).where(scanned_url_history.c.user_id == user_id)
    try:
        with engine.connect() as conn:
            row = conn.execute(statement).mappings().one()
            return {key: int(value or 0) for key, value in row.items()}
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not calculate scan statistics: {exc}") from exc

if __name__ == "__main__":
    try:
        create_scan_history_table()
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        print("MySQL connection successful!")
        print("Scanned_url_history table is ready.")
        print("No test scan was inserted.")
    except Exception as exc:
        print(f"Setup failed: {exc}")
    finally:
        engine.dispose()
'''
sql = -- Run this in MySQL Workbench. Uses the existing database.
USE phishing_database;

CREATE TABLE IF NOT EXISTS scanned_url_history (
    scan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    scanned_url TEXT NOT NULL,
    scan_result VARCHAR(50) NOT NULL,
    confidence_score FLOAT NULL,
    scan_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analysis_details JSON NULL,
    INDEX idx_user_scan_date (user_id, scan_date)
) ENGINE=InnoDB;
'''

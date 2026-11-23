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

SELECT * FROM scanned_url_history;
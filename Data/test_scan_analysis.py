from scan_analysis import (
    save_scan,
    get_user_scan_history,
    get_scan_by_id,
    get_scan_statistics,
    delete_scan
)

# Temporary testing IDs
user_a = "test_user_001"
user_b = "test_user_002"

# Save scans
scan_id = save_scan(
    user_id=user_a,
    scanned_url="https://example.com",
    scan_result="Legitimate",
    confidence_score=98.5,
    analysis_details={
        "dns_analysis": "Completed",
        "qr_scan": False
    }
)

save_scan(
    user_id=user_b,
    scanned_url="https://google.com",
    scan_result="Legitimate",
    confidence_score=99.0
)

# Retrieve User A's history
print("USER A HISTORY:")
print(get_user_scan_history(user_a))

# Retrieve User A's individual scan
print("INDIVIDUAL SCAN:")
print(get_scan_by_id(user_a, scan_id))

# Retrieve User A's statistics
print("USER A STATISTICS:")
print(get_scan_statistics(user_a))

# Test 1: User A should see only their records
history_a = get_user_scan_history(user_a)
print("User A records:", len(history_a))

# Test 2: User B should see only their records
history_b = get_user_scan_history(user_b)
print("User B records:", len(history_b))

# Test 3: User A should not access User B's scan
user_b_scan_id = 2
result = get_scan_by_id(user_a, user_b_scan_id)
print("Cross-user access:", result)

# Expected: None

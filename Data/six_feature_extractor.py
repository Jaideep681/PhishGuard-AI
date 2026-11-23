"""
Stage 6: URL and Redirect Feature Extraction (3)
Analyzes URL character patterns and HTTP redirects
to extract selected features used in phishing analysis.
Features:
- CharContinuationRate
- NoOfURLRedirect
- NoOfSelfRedirect
Security:
- Only HTTP and HTTPS URLs are accepted.
- Embedded URL credentials are rejected.
- Private, loopback and non-public IP addresses are blocked.
- Redirects are followed manually with a maximum of 10 hops.
- Request timeout is limited to 5 seconds.
IMPORTANT:
These are initial extraction implementations.
Validate every formula against the original PhiUSIIL
feature-generation methodology before model integration.
"""
from urllib.parse import urlsplit, urljoin
import requests
import ipaddress
import socket

def validate_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL cannot be empty")
    url = url.strip()
    if any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError("Invalid URL")
    if "://" not in url:
        url = "https://" + url
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only valid HTTP/HTTPS URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials are not allowed")
    _ = parsed.port
    return url, parsed

def is_public_host(host):
    try:
        addresses = socket.getaddrinfo(host, None)
        return bool(addresses) and all(
            ipaddress.ip_address(item[4][0]).is_global
            for item in addresses
        )
    except (socket.gaierror, ValueError):
        return False

def extract_stage6_features(url):
    url, parsed = validate_url(url)

    # 1. Character Continuation Rate (provisional formula)
    pairs = len(url) - 1
    continuation = sum(
        url[i].isalnum() and url[i + 1].isalnum()
        for i in range(max(0, pairs))
    )
    char_rate = round(continuation / pairs, 6) if pairs > 0 else 0.0

    # 2. URL and self redirect counts
    url_redirects = 0
    self_redirects = 0
    current_url = url
    original_host = parsed.hostname.lower()
    with requests.Session() as session:
        for _ in range(10):
            current = urlsplit(current_url)
            if not is_public_host(current.hostname):
                break
            try:
                response = session.get(
                    current_url,
                    timeout=5,
                    allow_redirects=False,
                    stream=True
                )
                try:
                    if response.status_code not in (301, 302, 303, 307, 308):
                        break
                    location = response.headers.get("Location")
                    if not location:
                        break
                    next_url, next_parsed = validate_url(
                        urljoin(current_url, location)
                    )
                    url_redirects += 1
                    if next_parsed.hostname.lower() == original_host:
                        self_redirects += 1
                    current_url = next_url
                finally:
                    response.close()
            except requests.RequestException:
                break
    return {
        "CharContinuationRate": char_rate,
        "NoOfURLRedirect": url_redirects,
        "NoOfSelfRedirect": self_redirects
    }

# Testing
if __name__ == "__main__":
    test_url = input("Enter URL to extract features: ")                          #"https://example.com/login"
    try:
        result = extract_stage6_features(test_url)
        for feature, value in result.items():
            print(f"{feature}: {value}")
        print("Total Stage 6 Features:", len(result))
    except (ValueError, requests.RequestException) as error:
        print("Error:", error)

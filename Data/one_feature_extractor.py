"""
Stage 1: PhiUSIIL URL Feature Extractor (1-11)
Extracts basic features directly from a URL.
IMPORTANT:
This is not yet the complete 50-feature input expected
by the existing trained ML model.
"""
import re
from ipaddress import ip_address as ip
from urllib.parse import urlsplit
def extract_url_features(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Please provide a valid URL.")
    url = url.strip()
    if any(ch.isspace() or ord(ch) < 32 for ch in url):
        raise ValueError("URL contains whitespace or control characters.")
    if "://" not in url:
        url = "https://" + url
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Only HTTP and HTTPS URLs are supported.")
        if not parsed.hostname:
            raise ValueError("Invalid hostname.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Embedded credentials are not allowed.")

        # Validate port
        _ = parsed.port
        hostname = parsed.hostname.rstrip(".").lower()

        # Check whether hostname is an IP address
        try:
            ip(hostname)
            is_ip = 1
        except ValueError:
            is_ip = 0

        # Split domain labels
        labels = hostname.split(".")
        if is_ip:
            tld = ""
            domain_length = len(hostname)
            subdomain_count = 0
        else:
            try:
                hostname = hostname.encode("idna").decode("ascii")
            except UnicodeError:
                raise ValueError("Invalid international domain name.")
            labels = hostname.split(".")
            if (
                len(hostname) > 253
                or any(
                    not label
                    or len(label) > 63
                    or label.startswith("-")
                    or label.endswith("-")
                    or not all(c.isalnum() or c == "-" for c in label)
                    for label in labels
                )
            ):
                raise ValueError("Invalid domain name.")
            tld = labels[-1]
            domain_length = len(hostname)
            subdomain_count = max(0, len(labels) - 2)

        # URL character counts
        letters = sum(ch.isalpha() for ch in url)
        digits = sum(ch.isdigit() for ch in url)
        features = {
            "URLLength": len(url),
            "DomainLength": domain_length,
            "IsDomainIP": is_ip,
            "TLDLength": len(tld),
            "NoOfSubDomain": subdomain_count,
            "NoOfLettersInURL": letters,
            "NoOfDegitsInURL": digits,
            "NoOfEqualsInURL": url.count("="),
            "NoOfQMarkInURL": url.count("?"),
            "NoOfAmpersandInURL": url.count("&"),
            "IsHTTPS": int(parsed.scheme.lower() == "https")
        }
        return features
    except ValueError as error:
        raise ValueError(str(error))

if __name__ == "__main__":
    user_url = input("Enter URL to extract features: ")
    try:
        result = extract_url_features(user_url)
        print("\nPHISHGUARD AI - STAGE 1 FEATURE EXTRACTION")
        print("-" * 50)
        for name, value in result.items():
            print(f"{name:<25}: {value}")
        print("\nExtracted feature count:", len(result))
    except ValueError as error:
        print("\nFeature extraction failed:", error)

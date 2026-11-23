from datetime import datetime, timezone
from ipaddress import ip_address
from urllib.parse import urlsplit
import dns.resolver
import dns.exception

DNS_LIFETIME_SECONDS = 5.0

def _parse_url(url):
    if not isinstance(url, str) or not url.strip():
        return None, "Invalid URL"
    value = url.strip()
    if any(ch.isspace() or ord(ch) < 32 for ch in value):
        return None, "Whitespace is not allowed"
    # Preserve explicitly supplied schemes

    if "://" in value:
        link = value
    else:
        link = "https://" + value
    try:
        parsed = urlsplit(link)

        # Accept only HTTP and HTTPS
        if parsed.scheme.lower() not in {"http", "https"}:
            return None, "Unsupported URL scheme"
        if not parsed.hostname:
            return None, "Invalid hostname"

        # Reject embedded credentials
        if parsed.username is not None or parsed.password is not None:
            return None, "Embedded credentials are not allowed"

        # Validate port
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            return None, "Invalid port"

        hostname = parsed.hostname.rstrip(".").lower()

        # Validate IP address or normalize domain
        try:
            ip_address(hostname)
            is_ip = True

        except ValueError:
            is_ip = False

            try:
                hostname = hostname.encode("idna").decode("ascii")
            except UnicodeError:
                return None, "Invalid international domain name"

        # Validate hostname
        if not hostname:
            return None, "Invalid hostname"

        # Validate domain labels only when input is not an IP
        if not is_ip:
            if len(hostname) > 253:
                return None, "Hostname is too long"
            labels = hostname.split(".")
            if any(
                not label
                or len(label) > 63
                or label.startswith("-")
                or label.endswith("-")
                or not all(c.isalnum() or c == "-" for c in label)
                for label in labels
            ):
                return None, "Invalid domain name"
        return {
            "input_url": value,
            "hostname": hostname,
            "scheme": parsed.scheme.lower(),
            "is_ip_address": is_ip
        }, None
    except (ValueError, UnicodeError):
        return None, "Invalid URL format"

def _query_record(hostname, record_type):
    try:
        answers = dns.resolver.resolve(
            hostname,
            record_type,
            lifetime=DNS_LIFETIME_SECONDS,
            raise_on_no_answer=False
        )
        records = [
            answer.to_text() for answer in answers
        ] if answers else []
        return {
            "status": "found" if records else "no_answer",
            "records": records,
            "error": None
        }
    except dns.resolver.NXDOMAIN:
        return {
            "status": "nxdomain",
            "records": [],
            "error": "DNS resolver reports that the domain does not exist."
        }
    except dns.resolver.NoAnswer:
        return {
            "status": "no_answer",
            "records": [],
            "error": None
        }
    except dns.resolver.NoNameservers:
        return {
            "status": "resolver_error",
            "records": [],
            "error": "No DNS nameserver returned an answer."
        }
    except dns.exception.Timeout:
        return {
            "status": "timeout",
            "records": [],
            "error": "DNS query timed out."
        }
    except (dns.exception.DNSException, OSError) as exc:
        return {
            "status": "error",
            "records": [],
            "error": str(exc)
        }

def analyze_domain_dns(url):
    parsed, error = _parse_url(url)
    now = datetime.now(timezone.utc).isoformat()
    if error:
        return {
            "success": False,
            "input_url": url,
            "hostname": None,
            "analysis_time_utc": now,
            "records": {},
            "indicators": [],
            "message": error
        }
    host = parsed["hostname"]
    result = {
        "success": True,
        "input_url": parsed["input_url"],
        "hostname": host,
        "scheme": parsed["scheme"],
        "is_ip_address": parsed["is_ip_address"],
        "analysis_time_utc": now,
        "records": {},
        "indicators": [],
        "message": "Analysis complete. DNS results are supporting evidence only."
    }

    # IP address handling
    if parsed["is_ip_address"]:
        result["indicators"].append({
            "name": "IP Address used directly",
            "severity": "informational",
            "detail": (
                "The URL uses an IP address instead of a domain name. "
                "This can be legitimate or suspicious depending on context."
            )
        })
        for record_type in ("A", "AAAA", "MX", "NS", "TXT"):
            result["records"][record_type] = {
                "status": "not_applicable",
                "records": [],
                "error": None
            }
        return result

    # DNS record lookup
    for record_type in ("A", "AAAA", "MX", "NS", "TXT"):
        result["records"][record_type] = _query_record(
            host, record_type
        )
    a = result["records"]["A"]
    aaaa = result["records"]["AAAA"]

    # Collect DNS indicators
    if a["records"] or aaaa["records"]:
        result["indicators"].append({
            "name": "Hostname resolves",
            "severity": "informational",
            "detail": (
                "DNS returned an IPv4 and/or IPv6 address. "
                "This does not prove the website is trustworthy."
            )
        })
    elif (
        a["status"] == "nxdomain"
        and aaaa["status"] == "nxdomain"
    ):
        result["indicators"].append({
            "name": "Domain did not resolve",
            "severity": "warning",
            "detail": (
                "The DNS resolver reported that the hostname does not exist. "
                "Resolver differences or temporary DNS issues are possible."
            )
        })
    elif (
        a["status"] in {"timeout", "resolver_error", "error"}
        or aaaa["status"] in {"timeout", "resolver_error", "error"}
    ):
        result["indicators"].append({
            "name": "DNS resolution could not be confirmed",
            "severity": "warning",
            "detail": (
                "The lookup failed or timed out. "
                "This alone is not proof of phishing."
            )
        })
    result["indicators"].append({
        "name": "DNS records require context",
        "severity": "informational",
        "detail": (
            "A, AAAA, MX, NS, and TXT records can support investigation, "
            "but record presence or absence alone cannot establish a phishing verdict."
        )
    })
    return result

if __name__ == "__main__":
    url = input("Enter a URL or domain to analyze: ").strip()
    print("\n===== PHISHGUARD AI DNS ANALYSIS =====")
    result = analyze_domain_dns(url)
    print(f"Success: {result['success']}")
    print(f"Hostname: {result['hostname']}")
    print(f"Message: {result['message']}")
    for kind, data in result["records"].items():
        print(f"\n{kind} status: {data['status']}")
        for record in data["records"]:
            print(f"  - {record}")
        if data["error"]:
            print(f"  Note: {data['error']}")
    print("\nIndicators:")
    for item in result["indicators"]:
        print(
            f"- [{item['severity'].upper()}] "
            f"{item['name']}: {item['detail']}"
        )


"""
Stage 5: Webpage Feature Extraction (11+7+7+3+18)
Fetches webpage HTML and extracts selected webpage-related
features used in phishing analysis.
Security:
- Only HTTP and HTTPS URLs are accepted.
- Private, loopback and reserved IP addresses are blocked.
- Redirects are disabled.
- Response size and timeout are limited.
IMPORTANT:
These are initial extraction implementations.
Validate every formula against the original PhiUSIIL
feature-generation methodology before model integration.
"""

import ipaddress
import socket
from urllib.parse import urlsplit, urljoin
import requests
from bs4 import BeautifulSoup
MAX_RESPONSE_SIZE = 2 * 1024 * 1024
REQUEST_TIMEOUT = 8
MAX_REDIRECTS = 5
def validate_public_url(url):

    """Validate URL and reject private or unsafe destinations."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")
    if not parsed.hostname:
        raise ValueError("Invalid hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing credentials are not allowed.")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid port.")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid port.")
    hostname = parsed.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(hostname)
        addresses = [hostname]
    except ValueError:
        try:
            records = socket.getaddrinfo(
                hostname,
                port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM
            )
        except socket.gaierror:
            raise ValueError("Hostname could not be resolved.")
        addresses = list({record[4][0] for record in records})
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(
                "Private, loopback or non-public destinations are blocked."
            )
    return parsed

def fetch_webpage(url):
    """
    Fetch a public webpage with manually validated redirects.

    Security:
    - Validates every redirect destination.
    - Allows only HTTP and HTTPS.
    - Blocks private and non-public IP destinations.
    - Limits redirects, response size and request timeout.
    - Does not automatically follow redirects.
    """
    headers = {
        "User-Agent": "PhishGuardAI-SecurityScanner/1.0"
    }
    current_url = url.strip()
    for redirect_count in range(MAX_REDIRECTS + 1):

        # Validate the initial URL and every redirect destination.
        validate_public_url(current_url)
        response = requests.get(
            current_url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
            stream=True
        )

        # Handle redirects manually.
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise ValueError(
                    "Redirect response does not contain a Location header."
                )
            if redirect_count >= MAX_REDIRECTS:
                raise ValueError("Maximum redirect limit exceeded.")

            # Resolve relative redirect destinations.
            next_url = urljoin(current_url, location)

            # Validate the next URL before making another request.
            validate_public_url(next_url)
            current_url = next_url
            continue

        # Handle unsuccessful HTTP responses.
        if response.status_code != 200:
            response.close()
            return None, current_url
        try:
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > MAX_RESPONSE_SIZE:
                        raise ValueError(
                            "Webpage is larger than the allowed size."
                        )
                except ValueError as error:
                    if str(error) == (
                        "Webpage is larger than the allowed size."
                    ):
                        raise
                    raise ValueError("Invalid Content-Length header.")

            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)
                if len(content) > MAX_RESPONSE_SIZE:
                    raise ValueError(
                        "Webpage exceeded the allowed size."
                    )
            html = bytes(content).decode(
                response.encoding or "utf-8",
                errors="replace"
            )
            final_url = response.url
            return html, final_url
        finally:
            response.close()
    raise ValueError("Unable to retrieve webpage.")

def extract_webpage_features(url):

    """Extract selected webpage-related features."""
    html, final_url = fetch_webpage(url)
    if html is None:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlsplit(final_url)

    # 1. LineOfCode
    lines = html.splitlines()
    line_of_code = len(lines)

    # 2. LargestLineLength
    largest_line_length = max((len(line) for line in lines),default=0)

    # 3. HasTitle
    title_tag = soup.find("title")
    title_text = title_tag.get_text(" ", strip=True) if title_tag else ""
    has_title = int(bool(title_text))

    ''' 4. DomainTitleMatchScore
    Provisional: exact normalized domain-name token match. '''
    domain_parts = parsed.hostname.lower().split(".")
    domain_tokens = {part for part in domain_parts if part and part not in {"www"}}
    title_tokens = set(title_text.lower().replace("-", " ").replace(".", " ").split())
    domain_title_match_score = (100.0 * len(domain_tokens & title_tokens) / len(domain_tokens) if domain_tokens else 0.0)

    # 5. HasFavicon
    favicon = soup.find(
        "link",
        rel=lambda value: value and "icon" in str(value).lower()
    )
    has_favicon = int(favicon is not None)

    # 6. Robots
    robots_meta = soup.find(
        "meta",
        attrs={"name": lambda value: value and value.lower() == "robots"}
    )
    robots = int(robots_meta is not None)

    # 7. IsResponsive
    viewport = soup.find(
        "meta",
        attrs={"name": lambda value: value and value.lower() == "viewport"}
    )
    is_responsive = int(viewport is not None)

    # 8. NoOfPopup
    ''' Static HTML cannot reliably identify JavaScript popups.
    This counts common popup-related HTML markers only. '''
    popup_markers = soup.select(
        '[role="dialog"], [aria-modal="true"], .popup, .modal'
    )
    no_of_popup = len(popup_markers)

    # 9. NoOfiFrame
    no_of_iframe = len(soup.find_all("iframe"))

    # 10. HasExternalFormSubmit
    has_external_form_submit = 0
    for form in soup.find_all("form"):
        action = form.get("action", "").strip()
        if not action:
            continue
        target = urlsplit(urljoin(final_url, action))
        if target.hostname and target.hostname.lower() != parsed.hostname.lower():
            has_external_form_submit = 1
            break

    # 11. HasSocialNet
    social_domains = (
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "tiktok.com"
    )
    has_social_net = int(
        any(
            any(domain in (tag.get("href") or "").lower()
                for domain in social_domains)
            for tag in soup.find_all("a", href=True)
        )
    )

    # 12. HasSubmitButton
    has_submit_button = int(
        bool(soup.find("button", attrs={"type": "submit"}))
        or bool(soup.find("input", attrs={"type": "submit"}))
    )

    # 13. HasHiddenFields
    has_hidden_fields = int(bool(soup.find_all("input", attrs={"type": "hidden"})))

    # 14. HasPasswordField
    has_password_field = int(bool(soup.find("input", attrs={"type": "password"})))

    # 15. HasCopyrightInfo
    page_text = soup.get_text(" ", strip=True).lower()
    has_copyright_info = int(
        "copyright" in page_text
        or "©" in page_text
        or "(c)" in page_text
    )

    # 16. NoOfImage
    no_of_image = len(soup.find_all("img"))

    # 17. NoOfCSS
    external_css = len(
        soup.find_all("link", rel=lambda value: (
            value and "stylesheet" in str(value).lower()
        ))
    )
    inline_css = len(soup.find_all("style"))
    no_of_css = external_css + inline_css

    # 18. NoOfJS
    external_js = len(soup.find_all("script", src=True))
    inline_js = len(soup.find_all("script", src=False))
    no_of_js = external_js + inline_js
    return {
        "LineOfCode": line_of_code,
        "LargestLineLength": largest_line_length,
        "HasTitle": has_title,
        "Title": title_text,
        "DomainTitleMatchScore": domain_title_match_score,
        "HasFavicon": has_favicon,
        "Robots": robots,
        "IsResponsive": is_responsive,
        "NoOfPopup": no_of_popup,
        "NoOfiFrame": no_of_iframe,
        "HasExternalFormSubmit": has_external_form_submit,
        "HasSocialNet": has_social_net,
        "HasSubmitButton": has_submit_button,
        "HasHiddenFields": has_hidden_fields,
        "HasPasswordField": has_password_field,
        "HasCopyrightInfo": has_copyright_info,
        "NoOfImage": no_of_image,
        "NoOfCSS": no_of_css,
        "NoOfJS": no_of_js
    }

if __name__ == "__main__":
    test_url = input("Enter URL to extract features: ")                          #https://example.com
    try:
        features = extract_webpage_features(test_url)
        print("\nPHISHGUARD AI - STAGE 5 FEATURE EXTRACTION")
        print("-" * 55)
        for name, value in features.items():
            print(f"{name}: {value}")
        print("-" * 55)
        print("Webpage features extracted:", len(features))
    except (ValueError, requests.RequestException) as error:
        print("Webpage analysis failed:", error)

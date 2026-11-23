"""
Security utilities: SSRF protection, URL validation, and Path Traversal guards.
"""
import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional


# Reserved / Private IP networks that should not be reached via university URL requests
DISALLOWED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local (Cloud metadata 169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local Address
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
]


def validate_university_url(url: str) -> Tuple[bool, str]:
    """
    Validate that user-provided URL is a safe public HTTP/HTTPS URL or demo schema,
    preventing SSRF attacks on localhost or internal network infrastructure.
    """
    if not url or not url.strip():
        return False, "URL cannot be empty."

    url = url.strip()

    # Allow demo/mock schema specifically for offline testing
    if url.startswith("demo://") or url.startswith("sample://"):
        return True, "Safe demo schema."

    # Parse URL
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Disallowed protocol scheme: '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL."

    # Block localhost string explicitly
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        # Exception: only allow localhost if port is clearly a designated local demo server
        return False, "Target URL points to a loopback address or internal hostname."

    # Resolve IP address to detect internal / private IPs (SSRF guard)
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            for net in DISALLOWED_NETWORKS:
                if ip_obj in net:
                    return False, f"Target IP '{ip_str}' is within a private or restricted network range."
    except socket.gaierror:
        # DNS could not resolve; permit URL if it's a known domain or report DNS warning
        pass
    except Exception as e:
        return False, f"URL security resolution error: {str(e)}"

    return True, "URL is safe."


def sanitize_job_id(job_id: str) -> str:
    """Validate and sanitize job_id against path traversal attacks."""
    if not job_id:
        raise ValueError("Invalid empty job_id.")
    clean = str(job_id).strip()
    if re.search(r"[^a-zA-Z0-9\-_]", clean):
        raise ValueError("Path traversal or illegal characters detected in job_id.")
    if len(clean) < 4 or len(clean) > 64:
        raise ValueError("Malformed job_id length.")
    return clean


def safe_filename(name: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    cleaned = re.sub(r"[^\w\-.]", "_", str(name))
    return cleaned.strip("._")

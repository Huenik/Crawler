import requests
import os
import re
from urllib.parse import urlparse

def sanitize_filename(url):
    """
    Produce a filesystem-safe filename from a URL.
    """
    parsed = urlparse(url)
    safe_path = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', parsed.path)

    if not safe_path or safe_path == "_":
        safe_path = "index"

    filename = f"{safe_path}__{parsed.netloc}"

    if parsed.query:
        query = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', parsed.query)
        filename += f"_{query}"

    if not filename.endswith(".html"):
        filename += ".html"

    return filename

def download_html(url, output_dir):
    """
    Download and save the HTML for a single URL into output_dir.
    """
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        filename = sanitize_filename(url)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[+] Saved {url} => {filepath}")
    except requests.exceptions.RequestException as err:
        print(f"[-] Failed to download {url}: {err}")

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

    # Example: "index__community.bistudio.com"
    filename = f"{parsed.netloc}__{safe_path}"

    if parsed.query:
        query = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', parsed.query)
        filename += f"_{query}"

    if not filename.endswith(".html"):
        filename += ".html"

    return filename

def download_html(url, output_dir):
    """
    Download and save the HTML for a single URL into output_dir.
    Append the URL->filename mapping to download_map.txt if successful.
    """
    filename = sanitize_filename(url)
    filepath = os.path.join(output_dir, filename)

    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[+] Saved {url} => {filepath}")

        # Log the mapping
        with open(os.path.join(output_dir, "download_map.txt"), "a", encoding="utf-8") as map_file:
            map_file.write(f"{url}\t{filename}\n")

    except requests.exceptions.RequestException as err:
        print(f"[-] Failed to download {url}: {err}")

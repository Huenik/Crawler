import requests
import argparse
import os
import re
from urllib.parse import urlparse


def sanitize_filename(url):
    #Produce a filesystem-safe filename from a URL

    parsed = urlparse(url)
    # Remove any characters from the path that might be invalid in filenames
    # and join with underscores
    safe_path = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', parsed.path)

    # If the path portion is empty, let's store it as 'index'
    if not safe_path or safe_path == "_":
        safe_path = "index"

    # Combine domain + path into one safe filename
    filename = f"{parsed.netloc}{safe_path}"

    # If query params exist, incorporate them as well
    if parsed.query:
        query = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', parsed.query)
        filename += f"_{query}"

    # Finally, append '.html' if it’s not already at the end
    if not filename.endswith(".html"):
        filename += ".html"

    return filename


def download_html(url, output_dir):
    """
    Download the HTML for a single URL and save it to a file in output_dir.
    """
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()  # Raise if the response has an HTTP error status code
        filename = sanitize_filename(url)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[+] Saved {url} => {filepath}")
    except requests.exceptions.RequestException as err:
        print(f"[-] Failed to download {url}: {err}")


def main():
    parser = argparse.ArgumentParser(
        description="Download HTML pages from a list of URLs and save them locally."
    )
    parser.add_argument(
        '-f', '--file',
        required=True,
        help="Path to the file containing URLs (one per line)."
    )
    parser.add_argument(
        '-o', '--output',
        default='downloaded_html',
        help="Directory to store downloaded HTML files (default: downloaded_html)."
    )
    args = parser.parse_args()

    # Create the output directory if it doesn't already exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # Read URLs from file
    with open(args.file, 'r', encoding='utf-8') as infile:
        for line in infile:
            url = line.strip()
            if not url:
                continue
            download_html(url, args.output)


if __name__ == "__main__":
    main()

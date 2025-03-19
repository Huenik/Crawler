#!/usr/bin/env python3
import argparse
import os
import sys
import time
import threading
import requests
from Crawler import WebCrawler
from Downloader import sanitize_filename  # Use to build filenames


# --- Spinner for crawling phase (unchanged) ---
def spinner_and_progress(crawler):
    spinner_chars = ["|", "\\", "-", "/"]
    idx = 0
    while not crawler.finished:
        visited = crawler.visited_count
        discovered = len(crawler.links)
        percent = (visited / discovered * 100) if discovered else 0
        sys.stdout.write(
            f"\rCrawling... {spinner_chars[idx % len(spinner_chars)]} "
            f"[Visited: {visited}/{discovered} ({percent:0.1f}%)]"
        )
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    sys.stdout.write("\rCrawling complete!                    \n")
    sys.stdout.flush()


# --- Spinner for download phase ---
def spinner_download(total, counter, finished_flag):
    spinner_chars = ["|", "\\", "-", "/"]
    idx = 0
    while not finished_flag["finished"]:
        count = counter["count"]
        percent = (count / total * 100) if total else 0
        sys.stdout.write(
            f"\rDownloading... {spinner_chars[idx % len(spinner_chars)]} "
            f"[Downloaded: {count}/{total} ({percent:0.1f}%)]"
        )
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    sys.stdout.write("\rDownloading complete!                      \n")
    sys.stdout.flush()


# --- Download all function with duplicate protection and image skipping ---
def download_all(links, output_dir, verbose):
    """
    Download each URL from 'links' into output_dir.
    In non-verbose mode, a spinner thread shows progress.
    Duplicate URLs (based on file existence) and image URLs are skipped.
    """
    total = len(links)
    if total == 0:
        return

    counter = {"count": 0}
    finished_flag = {"finished": False}
    spinner_thread = None
    if not verbose:
        spinner_thread = threading.Thread(target=spinner_download, args=(total, counter, finished_flag))
        spinner_thread.start()

    # Define image extensions to skip
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico')

    for link in links:
        # Skip non-http links
        if not link.startswith("http"):
            counter["count"] += 1
            continue

        # Skip URLs that appear to point to an image
        if link.lower().endswith(image_extensions):
            if verbose:
                print(f"[!] Skipping image URL: {link}")
            counter["count"] += 1
            continue

        filename = sanitize_filename(link)
        filepath = os.path.join(output_dir, filename)

        # Duplicate protection: if file exists, skip download.
        if os.path.exists(filepath):
            if verbose:
                print(f"[!] Duplicate found, skipping {link}")
            counter["count"] += 1
            continue

        try:
            response = requests.get(link, timeout=10, allow_redirects=True)
            response.raise_for_status()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)
            if verbose:
                print(f"[+] Saved {link} => {filepath}")
        except requests.exceptions.RequestException as err:
            if verbose:
                print(f"[-] Failed to download {link}: {err}")
        counter["count"] += 1

    finished_flag["finished"] = True
    if spinner_thread:
        spinner_thread.join()


def main():
    parser = argparse.ArgumentParser(
        description="Crawl a website with domain restrictions, then download pages with duplicate protection and image skipping."
    )
    parser.add_argument('-u', '--url', required=True, help="Starting URL to crawl.")
    parser.add_argument('-d', '--depth', type=int, default=2, help="Max recursion depth for same-domain links.")
    parser.add_argument('--outside-depth', type=int, default=1,
                        help="Max recursion depth for outside-domain links (default=1).")
    parser.add_argument('-o', '--output', default='downloaded_html', help="Directory to store downloaded HTML files.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output (no spinner).")
    args = parser.parse_args()

    # 1) Create and start the crawler.
    crawler = WebCrawler(
        url=args.url,
        max_depth=args.depth,
        outside_depth=args.outside_depth,
        verbose=args.verbose
    )
    spinner_thread = None
    if not args.verbose:
        spinner_thread = threading.Thread(target=spinner_and_progress, args=(crawler,))
        spinner_thread.start()
    crawler.start_crawling()
    if spinner_thread:
        spinner_thread.join()

    # 2) Create output directory if needed.
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 3) Download discovered links with progress spinner, duplicate protection, and image skipping.
    download_all(crawler.links, args.output, args.verbose)

    print(f"\nDone! Downloaded {len(crawler.links)} pages to '{args.output}'.")


if __name__ == "__main__":
    main()

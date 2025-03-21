#!/usr/bin/env python3
import argparse
import os
import sys
import time
import threading
import requests
from urllib.parse import urlparse
from Crawler import WebCrawler
from Downloader import sanitize_filename  # to build filenames

# --- Spinner for crawling phase ---
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

# --- Download all function with duplicate protection, image skipping, and map logging ---
def download_all(links, output_dir, verbose):
    """
    Download each URL from 'links' into output_dir.
    Skips non-http links, image URLs, and duplicates (if the file already exists).
    In non-verbose mode, a spinner shows progress.
    Logs each successful download to "download_map.txt".
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

    # Common image extensions to skip
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico')

    # Define the map file path and clear its contents
    map_file_path = os.path.join(output_dir, "download_map.txt")
    with open(map_file_path, "w", encoding="utf-8") as mf:
        mf.write("")

    for link in links:
        if not link.startswith("http"):
            counter["count"] += 1
            continue

        if link.lower().endswith(image_extensions):
            if verbose:
                print(f"[!] Skipping image URL: {link}")
            counter["count"] += 1
            continue

        filename = sanitize_filename(link)
        filepath = os.path.join(output_dir, filename)
        # Duplicate protection: skip if file exists.
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
            # Log the mapping for later combining
            with open(map_file_path, "a", encoding="utf-8") as mf:
                mf.write(f"{link}\t{filename}\n")
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
        description="Crawl a site, download with anti-duplicate and anti-image measures, restrict downloads to the target domain, and optionally combine output."
    )
    parser.add_argument('-u', '--url', required=True, help="Starting URL to crawl.")
    parser.add_argument('-d', '--depth', type=int, default=2, help="Max recursion depth for same-domain links.")
    parser.add_argument('--outside-depth', type=int, default=1,
                        help="Max recursion depth for outside-domain links (default=1).")
    parser.add_argument('-o', '--output', default='downloaded_html', help="Directory to store downloaded HTML files.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output (no spinner).")
    parser.add_argument('--combine', action='store_true', help="Run the combiner after downloads complete.")
    parser.add_argument('--parents', type=int, default=1,
                        help="Number of parent path segments to use for combining (default=1).")
    parser.add_argument('-r', '--restrict', action='store_true',
                        help="Restrict downloads to only pages on the target domain.")
    args = parser.parse_args()

    # 1) Create and start the crawler.
    crawler = WebCrawler(
        url=args.url,
        max_depth=args.depth,
        outside_depth=args.outside_depth,
        verbose=args.verbose
    )
    crawl_spinner = None
    if not args.verbose:
        crawl_spinner = threading.Thread(target=spinner_and_progress, args=(crawler,))
        crawl_spinner.start()
    crawler.start_crawling()
    if crawl_spinner:
        crawl_spinner.join()

    # 2) If restrict flag is set, filter the links to only those on the target domain.
    if args.restrict:
        target_netloc = crawler.parsed_self.netloc
        original_count = len(crawler.links)
        crawler.links = {link for link in crawler.links if urlparse(link).netloc == target_netloc}
        print(f"\nRestricted links from {original_count} to {len(crawler.links)} on the target domain.")

    # 3) Create output directory if it doesn't exist.
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 4) Download each discovered link with duplicate protection, image skipping, and log mapping.
    download_all(crawler.links, args.output, args.verbose)
    print(f"\nDone! Downloaded {len(crawler.links)} pages to '{args.output}'.")

    # 5) If the --combine flag is set, run the combiner.
    if args.combine:
        print("\nCombining downloaded files...")
        try:
            from Combiner import combine_all
            map_file = os.path.join(args.output, "download_map.txt")
            output_combined = os.path.join(args.output, "combined_html")
            if not os.path.exists(output_combined):
                os.makedirs(output_combined)
            combine_all(map_file=map_file, input_dir=args.output, output_dir=output_combined, parents=args.parents)
            print(f"Combined files saved in '{output_combined}'.")
        except ImportError:
            print("Combiner module not found. Skipping combination step.")

if __name__ == "__main__":
    main()

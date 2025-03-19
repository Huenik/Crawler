#!/usr/bin/env python3

import argparse
import os
import sys
import time
import threading

from Crawler import WebCrawler
from Downloader import download_html

def spinner_and_progress(crawler):
    """
    A background thread that shows a spinner plus rough progress info:
    - "visited_count / len(links)" ~ how many pages have been fetched out of how many discovered so far.
    """
    spinner_chars = ["|", "\\", "-", "/"]
    idx = 0

    while not crawler.finished:
        visited = crawler.visited_count
        discovered = len(crawler.links)
        if discovered == 0:
            percent = 0
        else:
            percent = (visited / discovered) * 100

        # Carriage return (\r) to overwrite the same line
        sys.stdout.write(
            f"\rCrawling... {spinner_chars[idx % len(spinner_chars)]}  "
            f"[Visited: {visited}/{discovered} ({percent:0.1f}%)]"
        )
        sys.stdout.flush()

        idx += 1
        time.sleep(0.2)

    # Once finished
    # Clear line (optional), then print a short message
    sys.stdout.write("\rCrawling complete!                      \n")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(
        description="Crawl a website (domain-based) with a spinner/progress or verbose logging, then download pages."
    )
    parser.add_argument('-u', '--url', required=True, help="Starting URL to crawl.")
    parser.add_argument('-d', '--depth', type=int, default=2, help="Max recursion depth for links in the same domain.")
    parser.add_argument('--outside-depth', type=int, default=1, help="Max recursion depth for outside links (default=1).")
    parser.add_argument('-o', '--output', default='downloaded_html', help="Directory to store downloaded HTML files.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output instead of spinner.")
    args = parser.parse_args()

    # 1) Create the crawler. Pass the verbose flag along so it can print or not.
    crawler = WebCrawler(
        url=args.url,
        max_depth=args.depth,
        outside_depth=args.outside_depth,
        verbose=args.verbose
    )

    # 2) If not verbose, start a separate thread for the spinner/progress
    spinner_thread = None
    if not args.verbose:
        spinner_thread = threading.Thread(target=spinner_and_progress, args=(crawler,))
        spinner_thread.start()

    # 3) Start crawling (blocks until recursion completes)
    crawler.start_crawling()

    # 4) Create output directory if needed
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 5) Download each discovered link
    for link in crawler.links:
        if link.startswith("http"):
            download_html(link, args.output)

    # 6) Wait for the spinner thread to exit if it was started
    if spinner_thread:
        spinner_thread.join()

    print(f"\nDone! Downloaded {len(crawler.links)} pages to '{args.output}'.")

if __name__ == "__main__":
    main()

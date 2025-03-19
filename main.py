#!/usr/bin/env python3

import argparse
import os
from Crawler import WebCrawler
from Downloader import download_html

def main():
    parser = argparse.ArgumentParser(
        description="Crawl a website, with a different outside-domain depth limit, and download discovered pages."
    )
    parser.add_argument(
        '-u', '--url',
        required=True,
        help="Starting URL to crawl."
    )
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=2,
        help="Max recursion depth for links that are inside the prefix."
    )
    parser.add_argument(
        '--outside-depth',
        type=int,
        default=1,
        help="Max recursion depth for links that are outside the prefix (default=1)."
    )
    parser.add_argument(
        '-o', '--output',
        default='downloaded_html',
        help="Directory to store downloaded HTML files."
    )
    args = parser.parse_args()

    # 1) Create the crawler with inside/outside depth settings
    crawler = WebCrawler(
        url=args.url,
        max_depth=args.depth,
        outside_depth=args.outside_depth
    )

    # 2) Start crawling
    crawler.start_crawling()

    # 3) Create output directory if needed
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 4) Download the HTML for each discovered link
    for link in crawler.links:
        # If it looks like a valid http link (starts with http)
        if link.startswith("http"):
            download_html(link, args.output)

    print("\nDone! Downloaded {} pages to '{}'.".format(len(crawler.links), args.output))

if __name__ == "__main__":
    main()

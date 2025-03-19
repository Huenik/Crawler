import argparse
import os
from Crawler import WebCrawler
from Downloader import download_html

def main():
    parser = argparse.ArgumentParser(
        description="Crawl a website and download the HTML of discovered pages."
    )
    parser.add_argument(
        '-u', '--url',
        required=True,
        help="Starting URL to crawl."
    )
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=1,
        help="Maximum recursion depth for the crawler."
    )
    parser.add_argument(
        '-o', '--output',
        default='downloaded_html',
        help="Directory to store downloaded HTML files."
    )
    args = parser.parse_args()

    # 1. Create and run the crawler
    crawler = WebCrawler(args.url, args.depth)
    crawler.start_crawling()  # Fills crawler.links with discovered URLs

    # 2. Create output directory if necessary
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 3. Download HTML from each discovered link
    for link in crawler.links:
        if link.startswith("http"):
            download_html(link, args.output)

    print("\nDone! Downloaded {} pages to '{}'.".format(len(crawler.links), args.output))

if __name__ == "__main__":
    main()

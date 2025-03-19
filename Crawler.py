import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self, url, max_depth, outside_depth=1):
        """
        :param url: Starting URL. We treat any URL with the same netloc (domain) as 'inside'.
        :param max_depth: Depth for links in the same domain.
        :param outside_depth: Depth for links outside the domain (default=1).
        """
        self.url = url.rstrip('/')  # uniform trailing slash
        self.max_depth = max_depth
        self.outside_depth = outside_depth

        # Parse the domain of the starting URL
        self.parsed_self = urlparse(self.url)

        # Store discovered links
        self.links = set()

    def start_crawling(self):
        """Begin crawling from self.url at depth=1."""
        self.crawl(self.url, depth=1)

    def is_within_domain(self, link):
        """
        Return True if 'link' is in the same domain (netloc) as self.url.
        """
        parsed_link = urlparse(link)
        return (parsed_link.netloc == self.parsed_self.netloc)

    def crawl(self, current_url, depth):
        """
        Recursively crawl 'current_url' up to the appropriate depth:
        - If it's within self.url's domain, up to self.max_depth.
        - Otherwise, up to self.outside_depth.
        """
        if self.is_within_domain(current_url):
            if depth > self.max_depth:
                return
        else:
            if depth > self.outside_depth:
                return

        try:
            response = requests.get(current_url, timeout=3, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as err:
            print(f"[-] Error fetching {current_url}: {err}")
            return

        for link_tag in soup.find_all('a'):
            href = link_tag.get('href')
            if href:
                full_link = urljoin(current_url, href)

                # Avoid re-crawling the same link
                if full_link not in self.links:
                    self.links.add(full_link)
                    self.crawl(full_link, depth + 1)

    def print_results(self):
        """Optional: Print discovered links."""
        print("Discovered Links:")
        for link in sorted(self.links):
            print(link)

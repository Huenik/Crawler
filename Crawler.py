import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self, url, max_depth, outside_depth=1):
        """
        :param url: The starting URL. We treat all URLs that share the same domain as 'inside'.
        :param max_depth: How many levels deep to crawl for URLs in the same domain.
        :param outside_depth: How many levels deep to crawl for URLs outside the domain (default=1).
        """
        # Remove trailing slash for uniform "startswith" comparisons later (if needed)
        self.url = url.rstrip('/')
        self.max_depth = max_depth
        self.outside_depth = outside_depth

        self.subdomains = set()
        self.links = set()
        self.jsfiles = set()

        # Parse domain of the starting URL
        self.parsed_self = urlparse(self.url)

    def start_crawling(self):
        """Begin crawling from self.url at depth=1."""
        self.crawl(self.url, depth=1)

    def is_within_domain(self, link):
        """
        Check if the discovered 'link' belongs to the same domain as self.url.
        Using only the netloc for domain comparison (e.g., "community.bistudio.com").
        """
        parsed_link = urlparse(link)
        return (parsed_link.netloc == self.parsed_self.netloc)

    def crawl(self, current_url, depth):
        """
        Recursively crawl 'current_url' up to the appropriate depth:
          - If it's within the same domain, we allow up to self.max_depth.
          - Otherwise, we allow up to self.outside_depth.
        """
        # Decide which depth limit to apply
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
            print(f"[-] An error occurred fetching {current_url}: {err}")
            return

        # Regex for capturing subdomains (optional usage)
        subdomain_query = r"https?://([a-zA-Z0-9.-]+)"

        for link_tag in soup.find_all('a'):
            href = link_tag.get('href')
            if href:
                # Convert relative href to a full absolute URL
                full_link = urljoin(current_url, href)

                # Optionally track subdomains
                if re.match(subdomain_query, href) and href not in self.subdomains:
                    self.subdomains.add(href)

                # Avoid re-crawling the same link
                if full_link not in self.links:
                    self.links.add(full_link)
                    self.crawl(full_link, depth + 1)

        # Optionally gather JS files
        for script_tag in soup.find_all('script'):
            script_src = script_tag.get('src')
            if script_src:
                self.jsfiles.add(script_src)

    def print_results(self):
        """
        Print discovered links, subdomains, and JS files.
        You can remove or modify as desired.
        """
        print("Discovered Links:")
        for link in sorted(self.links):
            print(link)

        if self.subdomains:
            print("\nDiscovered Subdomains:")
            for subdomain in sorted(self.subdomains):
                print(subdomain)

        if self.jsfiles:
            print("\nDiscovered JS Files:")
            for js in sorted(self.jsfiles):
                print(js)

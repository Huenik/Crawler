import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


class WebCrawler:
    def __init__(self, url, max_depth, outside_depth=1):
        """
        :param url: The starting URL (this also serves as the "prefix" if you want path-based restriction).
        :param max_depth: How many levels deep to crawl for URLs that are inside the prefix.
        :param outside_depth: How many levels deep to crawl for URLs that are outside the prefix (default=1).
        """
        # Remove trailing slash for uniform "startswith" comparisons later
        self.url = url.rstrip('/')
        self.max_depth = max_depth
        self.outside_depth = outside_depth

        self.subdomains = set()
        self.links = set()
        self.jsfiles = set()

    def start_crawling(self):
        """Begin the recursive crawling from self.url at depth = 1."""
        self.crawl(self.url, depth=1)

    def is_within_prefix(self, link):
        """
        Check if the discovered 'link' starts with the original self.url prefix.

        Example:
          If self.url = 'https://community.bistudio.com/wiki/Category:Arma_Reforger/Modding'
          and the link is 'https://community.bistudio.com/wiki/Category:Arma_Reforger/Modding/Assets'
          => returns True

          If link = 'https://www.mediawiki.org/wiki/date_picker'
          => returns False
        """
        return link.startswith(self.url)

    def crawl(self, current_url, depth):
        """
        Recursively crawl 'current_url' up to the appropriate max depth.
        - If it's within the prefix, we allow up to self.max_depth.
        - If it's outside the prefix, we allow up to self.outside_depth.
        """
        # Decide which depth limit to apply
        if self.is_within_prefix(current_url):
            if depth > self.max_depth:
                return
        else:
            # It's outside our prefix
            if depth > self.outside_depth:
                return

        try:
            response = requests.get(current_url, timeout=3, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as err:
            print(f"[-] An error occurred fetching {current_url}: {err}")
            return

        # Regex for capturing subdomains (optional example usage)
        subdomain_query = r"https?://([a-zA-Z0-9.-]+)"

        for link_tag in soup.find_all('a'):
            href = link_tag.get('href')
            if href:
                # Convert relative href to a full absolute URL
                full_link = urljoin(current_url, href)

                # Optionally track subdomains encountered
                if re.match(subdomain_query, href) and href not in self.subdomains:
                    self.subdomains.add(href)

                # Avoid re-crawling the same link
                if full_link not in self.links:
                    self.links.add(full_link)
                    # Recurse one level deeper
                    self.crawl(full_link, depth + 1)

        # Optionally gather JS files
        for script_tag in soup.find_all('script'):
            script_src = script_tag.get('src')
            if script_src:
                self.jsfiles.add(script_src)

    def print_results(self):
        """
        Print discovered links, subdomains, and JS files.
        Feel free to customize or remove if not needed.
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

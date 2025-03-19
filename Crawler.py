# original code written by calc1f4r @ https://github.com/calc1f4r/Recusive-web-crawler/
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class WebCrawler:
    def __init__(self, url, max_depth):
        self.url = url
        self.max_depth = max_depth
        self.subdomains = set()
        self.links = set()
        self.jsfiles = set()

    def start_crawling(self):
        self.crawl(self.url, depth=1)

    def crawl(self, url, depth):
        if depth > self.max_depth:
            return

        try:
            response = requests.get(url, timeout=3, allow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as err:
            print(f"[-] An error occurred: {err}")
            return

        subdomain_query = r"https?://([a-zA-Z0-9.-]+)"

        for link in soup.find_all('a'):
            link_text = link.get('href')
            if link_text:
                # Collect subdomains or direct links
                if re.match(subdomain_query, link_text) and link_text not in self.subdomains:
                    self.subdomains.add(link_text)
                else:
                    full_link = urljoin(url, link_text)
                    if full_link != url and full_link not in self.links:
                        self.links.add(full_link)
                        self.crawl(full_link, depth + 1)

        for file in soup.find_all('script'):
            script_src = file.get('src')
            if script_src:
                self.jsfiles.add(script_src)

    def print_results(self):
        # Example: Print collected links
        if self.links:
            for link in self.links:
                if link.startswith("http"):
                    print(link)

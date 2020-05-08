import requests
import re
from itertools import cycle
from urllib.parse import urlparse
from lxml.html import fromstring

class Crawler(object):
    def __init__(self, starting_url, output_file, ignore=None, include=None, template=None, rotate_proxies=False):
        self.starting_url = starting_url
        self.output_file = output_file
        self.visited = set()
        self.ignore_set = ignore or set(['mailto','google','youtube','twitter','ahSrt'])
        self.include_set = include
        self.links_found = list()
        self.template = re.compile(template)
        self.rotate_proxies = rotate_proxies
        
        if rotate_proxies:
            self.proxy_pool = cycle(self.get_proxies())

    def get_html(self, url):
        """get html code of a link

        Arguments:
            url {string} -- link url to parse

        Returns:
            string -- html code
        """        
        try:
            proxy_dict = None
            if self.rotate_proxies:
                proxy = next(self.proxy_pool)
                proxy_dict = {"http": proxy, "https": proxy}
                print(f'Use proxy {proxy}')

            html = requests.get(url,proxies=proxy_dict)
            if html.status_code == 200:
                return html.content.decode('latin-1')
            else:
                print(html.status_code )

        except Exception as e:
            raise(e)
            return ''
        
    def get_links(self, url):
        """extract links from webpage

        Arguments:
            url {string} -- link url

        Returns:
            set -- set of new links found on page
        """        
        html = self.get_html(url)
        parsed = urlparse(url)
        base = f'{parsed.scheme}://{parsed.netloc}'    
        links = re.findall('''<a\s+(?:[^>]*?\s+)?href="([^"]*)"''', html)    
        for i, link in enumerate(links):    
            if not urlparse(link).netloc:    
                link_with_base = base + link    
                links[i] = link_with_base

        clean_set = set(filter(lambda x: all([s not in x for s in self.ignore_set]), links))
        return set(filter(lambda x: all([s in x for s in self.include_set]), clean_set))

    def extract_info(self, url):
        """extract data from page

        Arguments:
            url {string} -- link url

        Returns:
            string -- data
        """        
        html = self.get_html(url)    
        meta = re.findall("<meta .*?name=[\"'](.*?)['\"].*?content=[\"'](.*?)['\"].*?>", html)    
        return dict(meta) 

    def crawl(self, url):
        """iterate recursively over all in links in a page

        Arguments:
            url {string} -- link url
        """        
        for link in self.get_links(url):
            if link in self.visited:
                continue

            if (self.template is None) or (len(re.findall(self.template ,link)) > 0):
                print(link)
                self.links_found.append(link)
                self.visited.add(link)
                # info = self.extract_info(link)
                
                with open(self.output_file, "a+") as f:
                    f.write(link)
                    f.write('\n')

            self.crawl(link)

    def start(self):
        # create output file
        open(self.output_file ,'w+')
        self.crawl(self.starting_url)

    # TODO: free proxies are mostly useless. Either blacklisted or dead
    def get_proxies(self):
        url = 'https://sslproxies.org/' # 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = fromstring(response.text)
        proxies = set()
        for i in parser.xpath('//tbody/tr')[:10]:
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                #Grabbing IP and corresponding PORT
                proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxies.add(proxy)
        return proxies

if __name__ == '__main__':
    crawler = Crawler(
        'https://www.mahag.de/gebrauchte/fahrzeugsuche/',
        output_file='/home/leon/Documents/repos/car-prices-analysis/crawler/links.csv',
        include=['https://www.mahag.de/gebrauchte/fahrzeugsuche/'],
        template='.*html&ahId=\d+',
        rotate_proxies=False
    )

    crawler.start()




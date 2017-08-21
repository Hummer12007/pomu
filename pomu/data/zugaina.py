"""
gpo.zugaina.org searcher and fetcher
"""
import lxml.html
import requests

from pomu.data.datasource import DataSource

BASE_URL = 'https://gpo.zugaina.org/'
SBASE_URL = BASE_URL + 'Search?search={}&page={}'

class ZugainaDataSource(DataSource):

    def __init__(self, query):
        self.query = query
        self.pagecache = {}
        self.itemcache = {}
        self.pagecount = -1

    def page_count(self):
        if self.pagecount > 0:
            return self.pagecount
        text = self.fetch_page(1)
        doc = lxml.html.document_fromstring(text)
        field = doc.xpath('//div[@class="pager"]/span')[0].text
        self.pagecount = (int(field.split(' ')[-1]) + 49) // 50
        return self.pagecount

    def get_page(self, page):
        text = self.fetch_page(page)
        doc = lxml.html.document_fromstring(text)
        return [(x.text.strip(), x.getchildren()[0].text)
                for x in doc.xpath('//div[@id="search_results"]/a/div')]

    def list_items(self, ident):
        text = self.fetch_item(ident)
        doc = lxml.html.document_fromstring(text)
        res = []
        for div in doc.xpath('//div[@id="ebuild_list"]/ul/div'):
            id_ = div.xpath('li/a')[0].get('href').split('/')[3]
            pv = div.xpath('li/div/b')[0].text
            overlay = div.xpath('@id')
            res.append((id_, pv, overlay))
        return res

    def get_item(self, ident):
        return requests.get(BASE_URL + 'AJAX/Ebuild/' + str(ident)).text

    def fetch_item(self, ident):
        if ident in self.itemcache:
            return self.itemcache[ident]
        res = requests.get(BASE_URL + ident).text
        return res


    def fetch_page(self, page):
        if page in self.pagecache:
            return self.pagecache[page]
        res = requests.get(SBASE_URL.format(self.query, page)).text
        self.pagecache[page] = res
        return res

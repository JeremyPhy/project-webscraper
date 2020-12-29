import json
import re
import time

from urllib.parse import urlsplit
from urllib import request
import urllib
from bs4 import BeautifulSoup

SLACK_CHANNEL = "XXXXXXXXX"
SLACK_API_KEY = "XXXXXXXXX"

class SlackBot(object):
    def __init__(self):
        self.url = 'https://slack.com/api/chat.postMessage'
        self.token = SLACK_API_KEY
        self.channel = SLACK_CHANNEL

    def postMessage(self, text):
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json;charset=UTF-8',
        }

        data = {
            'token': self.token,
            'channel': self.channel,  # Channel/User ID.
            'text': text
        }

        req = urllib.request.Request(url=self.url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        resp = urllib.request.urlopen(req, timeout=30)
        resp = json.loads(resp.read())
        if 'error' in resp:
            print(json.dumps(resp, indent=4, sort_keys=True))
            return False
        return True

class Monitor(object):
    def __init__(self, url):
        self.url = url
        self.host = '{uri.netloc}'.format(uri=urlsplit(url))
        self.path = '{uri.path}?{uri.query}#{uri.fragment}'.format(uri=urlsplit(url))

    def check_stock(self):
        pass

    def get_page(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
            "Cache-Control": "no-cache"
        }

        req = urllib.request.Request(url=self.url, headers=headers, method="GET")
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read()

    def itemIsInStock(self, stockInfo, priceInfo):
        if stockInfo:
            bad = ['sold', 'sold out', 'out of stock', 'unavailable',
                   'coming soon', 'backorder', 'back order',
                   'currently sold out',
                   'not available']
            for item in bad:
                if isinstance(stockInfo, str):
                    if stockInfo.lower().find(item) >= 0:
                        return False
                elif stockInfo.text.strip().lower().find(item) >= 0:
                    return False
            return True
        return False

    def notifyStock(self, soup, stockInfo, priceInfo):
        if self.itemIsInStock(stockInfo=stockInfo, priceInfo=priceInfo):
            stock_bot = SlackBot()

            if isinstance(self, BestBuyMonitor):
                text = 'Item in Stock: {0}\n\t{1}\n\t{2}\n\t{3}\n\t{4}'.format(self.title,
                                                                 soup.title.text.strip(),
                                                                 stockInfo.text.strip(),
                                                                 priceInfo.attrs['content'].strip(),
                                                                 self.url)
                stock_bot.postMessage(text)
            else:
                text = 'Item in Stock: {0}\n\t{1}\n\t{2}\n\t{3}\n\t{4}'.format(self.title,
                                                                 soup.title.text.strip(),
                                                                 stockInfo.text.strip(),
                                                                 priceInfo.text.replace('Only', '').strip(),
                                                                 self.url)
                stock_bot.postMessage(text)

    def onError(self, error):
        print('ERROR: ' + error)
        # stock_bot = SlackBot()
        # stock_bot.postMessage("Error: {0}\n" + error);


class NewEggMonitor(Monitor):
    def __init__(self, url):
        super(NewEggMonitor, self).__init__(url=url)
        self.title = "New Egg"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('div.row-side .flags-body')
        priceInfo = soup.select_one('li.price-current')
        if stockInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), stockInfo.text.strip())
        if priceInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip())
        if soup.select_one('div.g-recaptcha'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')

        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class MemoryExpressMonitor(Monitor):
    def __init__(self, url):
        super(MemoryExpressMonitor, self).__init__(url=url)
        self.title = "Memory Express"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('div.c-capr-inventory__availability > span')
        priceInfo = soup.select_one('div.GrandTotal > div')
        if stockInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), stockInfo.text.strip())
        if priceInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.text.replace('Only', '').strip())
        if soup.select_one('div.g-recaptcha'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class BHPhotoVideoMonitor(Monitor):
    def __init__(self, url):
        super(BHPhotoVideoMonitor, self).__init__(url=url)
        self.title = "B&H Photo-Video"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('span[data-selenium="stockStatus"]')
        priceInfo = soup.select_one('div[data-selenium="pricingPrice"]')
        if stockInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), stockInfo.text.strip())
        if priceInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip())
        if soup.select_one('div.g-recaptcha'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class CanadaComputersMonitor(Monitor):
    def __init__(self, url):
        super(CanadaComputersMonitor, self).__init__(url=url)
        self.title = "Canada Computers"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('button[id="btn-addCart"]')
        priceInfo = soup.select_one('div.order-2.order-md-1')
        onlineStatus = soup.select_one('div.pi-prod-availability > span')
        inStoreStatus = soup.select_one('div.pi-prod-availability > span.pl-2')
        alternateStockInfo = soup.select_one('p[id="storeinfo"]')

        if stockInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Available Online')
        if priceInfo and onlineStatus and inStoreStatus:
            self.notifyStock(soup=soup, stockInfo=onlineStatus, priceInfo=priceInfo)
            self.notifyStock(soup=soup, stockInfo=inStoreStatus, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}\n\t{3}\n\t{4}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip(),
                                                             onlineStatus.text.strip(), inStoreStatus.text.strip())

        if priceInfo and onlineStatus:
            self.notifyStock(soup=soup, stockInfo=onlineStatus, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}\n\t{3}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip(),
                                                             onlineStatus.text.strip())

        if priceInfo and inStoreStatus:
            self.notifyStock(soup=soup, stockInfo=inStoreStatus, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}\n\t{3}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip(),
                                                              inStoreStatus.text.strip())

        if alternateStockInfo:
            self.notifyStock(soup=soup, stockInfo=alternateStockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), alternateStockInfo.text.strip())

        if soup.select_one('div.g-recaptcha'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class BestBuyMonitor(Monitor):
    def __init__(self, url):
        super(BestBuyMonitor, self).__init__(url=url)
        self.title = "Best Buy"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('button.addToCartButton:disabled')
        priceInfo = soup.select_one('meta[itemProp="price"]')

        if stockInfo and priceInfo:
            self.notifyStock(soup=soup, stockInfo='Out of Stock', priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}\n\t{3}'.format(self.title, soup.title.text.strip(), 'Out of Stock', priceInfo.attrs['content'].strip())
        if stockInfo:
            self.notifyStock(soup=soup, stockInfo='Out of Stock', priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Out of Stock')
        if priceInfo:
            self.notifyStock(soup=soup, stockInfo=stockInfo, priceInfo=priceInfo)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.attrs['content'].strip())
        if soup.select_one('div.g-recaptcha'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class WalmartMonitor(Monitor):
    def __init__(self, url):
        super(WalmartMonitor, self).__init__(url=url)
        self.title = "Walmart"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('button[data-automation="cta-button"]:disabled')
        priceInfo = soup.select_one('span[data-automation="buybox-price"]')
        if stockInfo:
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), stockInfo.text.strip())
        if priceInfo:
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip())

        pattern = re.compile(r'PRELOADED', re.MULTILINE | re.DOTALL)
        stockJSON = soup.find("script", text=pattern)
        if stockJSON:
            prefix = 'PRELOADED_STATE__='
            suffix = '};'
            js = stockJSON.string

            startIndex = js.find(prefix)
            endIndex = js.find(suffix)

            if startIndex >= 0 and endIndex > startIndex:
                pageConfig = json.loads(js[startIndex + len(prefix):-1])
                storeStatus = 'Out of Stock'
                onlineStatus = 'Out of Stock'

                sku = pageConfig['product']['activeSkuId']
                if sku:
                    dimensions = pageConfig['entities']['skus'][sku]["endecaDimensions"]
                    for dimension in dimensions:
                        if dimension['name'] == 'StoreStatus':
                            storeStatus = dimension['value']
                        if dimension['name'] == 'OnlineStatus':
                            onlineStatus = dimension['value']

                    #print(json.dumps(pageConfig, indent=4, sort_keys=True))
                    self.notifyStock(soup=soup, stockInfo=storeStatus, priceInfo=priceInfo)
                    self.notifyStock(soup=soup, stockInfo=onlineStatus, priceInfo=priceInfo)
                    return '{0}:\n\t{1}\n\t{2}\n\t{3}'.format(self.title, soup.title.text.strip(),
                                                       'Store Availability - ' + storeStatus,
                                                       'Online Availability - ' + onlineStatus)

        if soup.select_one('div.g-recaptcha') or soup.select_one('div[id=px-captcha]'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')

class EBGamesMonitor(Monitor):
    def __init__(self, url):
        super(EBGamesMonitor, self).__init__(url=url)
        self.title = "EB Games"

    def __str__(self):
        soup = BeautifulSoup(self.get_page(), "html.parser", from_encoding="utf-8")
        stockInfo = soup.select_one('a.megaButton.buyDisabled')
        priceInfo = soup.select_one('span.pricetext')
        if stockInfo:
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), stockInfo.text.strip())
        if priceInfo:
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), priceInfo.text.strip())

        if soup.select_one('div.g-recaptcha') or soup.select_one('div[id=px-captcha]'):
            self.onError("Help.. Recaptcha Detected! " + self.url)
            return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Recaptcha Detected')
        self.onError("Help.. Invalid URL: " + self.url)
        return '{0}:\n\t{1}\n\t{2}'.format(self.title, soup.title.text.strip(), 'Invalid URL')


def parseUrlsToMonitor(urls):
    classes = {
        "newegg": NewEggMonitor,
        "memoryexpress": MemoryExpressMonitor,
        "bhphotovideo": BHPhotoVideoMonitor,
        "canadacomputers": CanadaComputersMonitor,
        "bestbuy": BestBuyMonitor,
        "walmart": WalmartMonitor,
        'ebgames': EBGamesMonitor
    }

    result = []

    for url in urls:
        host = '{uri.netloc}'.format(uri=urlsplit(url)).lower()
        for (key, value) in classes.items():
            if host.lower().find(key) >= 0:
                result.append(value(url))
    return result

if __name__ == '__main__':
    urls = [
        # "https://www.newegg.ca/amd-ryzen-9-5950x/p/N82E16819113663",    #AMD 5950X
        # "https://www.memoryexpress.com/Products/MX00114450",            #AMD 5950X
        # "https://www.bhphotovideo.com/c/product/1598372-REG/amd_100_100000059wof_ryzen_9_5950x_3_4.html",  #AMD 5950X
        # "https://www.canadacomputers.com/product_info.php?cPath=4_64_1969&item_id=183427",                 #AMD 5950X

        # "https://www.newegg.ca/p/N82E16868110294",                                          # PS5
        #"https://www.walmart.ca/en/ip/playstation5-console/6000202198562",                  # PS5
        # "https://www.ebgames.ca/PS5/Games/877522/playstation-5",  # PS5
        # "https://www.ebgames.ca/PS5/Games/877523/playstation-5-digital-edition",  # PS5
        # "https://www.bestbuy.ca/en-ca/product/playstation-5-console-online-only/14962185",  #PS5

        #"https://www.walmart.ca/en/ip/xbox-series-x-console-with-xbox-wireless-controller-robot-white-bundle-xbox-series-x/6000202298337" #XBSX
    ]

    monitors = parseUrlsToMonitor(urls)

    while True:
        for monitor in monitors:
            try:
                print(str(monitor) + '\n')
            except urllib.error.HTTPError as e:
                print(str(e))
        time.sleep(5)

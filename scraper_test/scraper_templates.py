from datetime import datetime
import httpx
import json
from bs4 import BeautifulSoup
import re
from lxml import etree #type:ignore
from urllib.parse import quote_plus


class scraperExampleTemplatePOST:
    """
    Class instance is assigned per target after match.
    In the class you can define how the scraper should perform.
    Add a function do_request() for custom code. 
    """
    def __init__(self, timeout, selector):
        self.name:str = "scraper_ex_POST"
        self.scraper_url: str = "https://cool.scraper.com/api/endpoint"
        self.scraper_headers: dict[str, str] ={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic abcdefghi"
        }
        self.timeout = timeout
        self.selector = selector

    def __str__(self):
        return self.name

    async def do_request(self, url: str):
        time_start = datetime.now()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.scraper_url,
                headers = self.scraper_headers,
                json = {
                    "url": url,
                    "headless": "yes",
                    "other_param": False
                }
            )
            response_time = (datetime.now() - time_start).total_seconds()
            status = response.status_code
            body = await response.aread()
            response_size = len(body)

        title, selector = self.parse(body)

        result = {
            "ts": time_start.replace(microsecond=0).isoformat(),
            "url": url,
            "status": status,
            "response_time": response_time,
            "response_size": response_size,
            "title": title,
            "selector": selector 
        }
        return result
        
    def parse(self, body: str | bytes) -> tuple[str, bool]:

        title = ""
        selector_found = False
        html = ""
        try:
            html = body.decode('utf-8') #type:ignore
        except:
            html = body
        # or json loads body, then grab html
        try:
            soup = BeautifulSoup(body, 'html.parser') # note: if decoding needed then pass decoded `html` var from above
            # title:
            try:
                title = soup.title.string 
            except:
                try:
                    title_search = re.search('<title>(.*)</title>', body.decode('utf-8'), re.IGNORECASE) #type:ignore
                    if title_search:
                        title = title_search.group(1)
                except:
                    title = "Not found"
            # selector
            try:
                selector_elem = soup.select(self.selector)
                if selector_elem:
                    selector_found = True
            except:
                selector_found = False
        except:
            title = "Not found"
            selector_found = False

        return title, selector_found


class scraperExampleTemplateGET:
    """
    class instance is assigned per target after match
    in the class you can define how the scraper should perform
    add a function do_request(), custom code goes there
    """
    def __init__(self, timeout, selector):
        self.name:str = "scraper_ex_GET"
        self.scraper_url: str = "https://cool.scraper.com/api/endpoint"
        self.scraper_headers: dict[str, str] ={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic abcdefghi"
        }
        self.timeout = timeout
        self.selector = selector

    def __str__(self):
        return self.name

    async def do_request(self, url: str):
        time_start = datetime.now()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.scraper_url,
                timeout=self.timeout,
                params={
                    'apiKey': 'abcederfhg',
                    'url': url,
                    'render': False
                },
                headers = self.scraper_headers
            )
            response_time = (datetime.now() - time_start).total_seconds()
            status = response.status_code
            body = await response.aread()
            response_size = len(body)
        
            title, selector = self.parse(body)
    
            result = {
                "ts": time_start.replace(microsecond=0).isoformat(),
                "url": url,
                "status": status,
                "response_time": response_time,
                "response_size": response_size,
                "title": title,
                "selector": selector 
            }
            return result
            
    def parse(self, body: str | bytes) -> tuple[str, bool]:
        pass
        #<-- code -->

class scraperExampleTemplateGETURL:
    """
    class instance is assigned per target after match
    in the class you can define how the scraper should perform
    add a function do_request(), custom code goes there
    """
    def __init__(self, timeout, selector):
        self.name:str = "scraper_ex_get_by_url"

        self.timeout = timeout
        self.selector = selector

    def __str__(self):
        return self.name

    async def do_request(self, url: str):
        time_start = datetime.now()
        scraper_url = f"https://api.scraper-that-wants-to-be-get-by-url.com/?token=asbx&url={quote_plus(url)}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                scraper_url,
                timeout=self.timeout,
                params={},
                headers={},
            )
            response_time = (datetime.now() - time_start).total_seconds()
            status = response.status_code
            body = await response.aread()
            response_size = len(body)
        
            title, selector = self.parse(body)
    
            result = {
                "ts": time_start.replace(microsecond=0).isoformat(),
                "url": url,
                "status": status,
                "response_time": response_time,
                "response_size": response_size,
                "title": title,
                "selector": selector 
            }
            return result
            
    def parse(self, body: str | bytes) -> tuple[str, bool]:
        pass
        #<-- code -->

class scraperExampleTemplatePROXY:
    """
    class instance is assigned per target after match
    in the class you can define how the scraper should perform
    add a function do_request(), custom code goes there
    """
    def __init__(self, timeout, selector):
        self.name:str = "scraper_ex_Proxy"
        self.scraper_headers: dict[str, str] ={}
        self.timeout = timeout
        self.selector = selector

    def __str__(self):
        return self.name

    async def do_request(self, url: str):
        time_start = datetime.now()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxy=f"http://user:pass@scraper.proxy.com:10000",
            ) as client:
            response = await client.get(
                url,
                timeout=self.timeout,
                headers=self.scraper_headers,
                follow_redirects=True
            )
            response_time = (datetime.now() - time_start).total_seconds()
            status = response.status_code
            body = await response.aread()
            response_size = len(body)
        
            title, selector = self.parse(body)
    
            result = {
                "ts": time_start.replace(microsecond=0).isoformat(),
                "url": url,
                "status": status,
                "response_time": response_time,
                "response_size": response_size,
                "title": title,
                "selector": selector 
            }
            return result
            
    def parse(self, body: str | bytes) -> tuple[str, bool]:
        pass
        #<-- code -->
import asyncio
import logging
from typing import Any
import click, enum

from .requests_controller import RequestsController
from .url_loader import URLLoader
from .sql_writer import SQLWriter

from .scraper_templates import scraperExampleTemplatePOST, scraperExampleTemplateGET,

#test params
TOTAL_REQUESTS = 1000
INTERVAL_SECONDS = 1.0 #unused
TIMEOUT = 60.0

def scraper_setup(target: str) -> tuple[str, Any]:
    """
    Match the targets to scrapers imported from the scraper_templates module.
    Selectors used for confirming a successful scrape are also set here.
    It is not neccessary to modify the code past this function. Everthing else
    is set up with click/CLI args.
    """
    url_file = ""
    scraper = None
    match target:
        case "example":
            url_file = "urls/example.txt"
            selector = "body div h1" # CSS selector checked by scraper.parse() to confirm a successful scrape
            #scraper = scraperExampleTemplatePOST(timeout=TIMEOUT, selector=selector)
            scraper = scraperExampleTemplatePOST(timeout=TIMEOUT, selector=selector)
        case "httpbin":
            url_file = "urls/httpbin.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplatePOST(timeout=TIMEOUT, selector=selector)
        # The following are not yet differentiated:
        case "google":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "allegro":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "amazon":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "chatgpt":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "g2":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "hyatt":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "instagram":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "lowes":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "nordstrom":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "shein":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "tiktok":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
        case "walmart":
            url_file = "urls/url_testfile.txt"
            selector = "placeholder"
            scraper = scraperExampleTemplateGET(timeout=TIMEOUT, selector=selector)
    # not adding wildcard, click choice will not let undefined target pass.
    # both have to be in sync.
    return url_file, scraper

def _set_logging(filename: str) -> None:
    logging.basicConfig(level=logging.DEBUG)

class TestController:
    def __init__(self, req_controller: RequestsController, target: str, requests:int = TOTAL_REQUESTS):
        self.req_controller = req_controller # shared RequestsController instance that will actually dispatch/batch the submitted scraping jobs.
        self.target = target
        self.requests_ttl = requests
        self.url_file, self.scraper = scraper_setup(target)

        # Load all URLs for this target into memory and get an infinite,
        # cycling iterator over them (see URLLoader.__iter__).
        self.url_loader = URLLoader(self.url_file)
        self.url_stream = iter(self.url_loader)

    def fetch_next_url(self) -> str:
        return next(self.url_stream)

    async def req_loop(self):
    # Submits scraper instance, target and url (all three = one scraping job) to the RequestsController
    # then iterate and yield the next url until requests_ttl is reached.
        for i in range(self.requests_ttl):
            url = self.fetch_next_url()
            await self.req_controller.submit({"scraper": self.scraper, "target": self.target, "url": url})
            #await asyncio.sleep(0.1) # pacing is off here, left to RequestsController



async def start_test(target:str, rate:int, requests: int, db_filename:str) -> None:
    with SQLWriter(db_filename) as db:
        async def request_fn(item: dict): 
            # item is dict {scraper, target, url}
            # This is the function RequestsController actually calls per item
            result = await item["scraper"].do_request(item["url"])
            # item["scraper"].do_request(url) is the do_request() function in
            # the scraper setup class
            
            db.add(
                target=item["target"],
                scraper=item["scraper"].name,
                ts = result["ts"],
                status = result["status"],
                response_time = result["response_time"],
                response_size = result["response_size"],
                selector = result["selector"],
                title = result["title"],
                url = item["url"]
                )
            

        controller = RequestsController(
            request_fn=request_fn,
            batch_size=rate,
            #interval=INTERVAL_SECONDS
        )
        controller.start()

        test = TestController(controller, target = target, requests = requests)

        await test.req_loop()

        # Signals the controller to stop accepting new work and waits for all
        # already queued batches to finish (see RequestsController.stop).
        await test.req_controller.stop()

# For CLI
class TargetsClick(enum.Enum):
    # Must be kept in sync with the `match target` cases in scraper_setup();
    # click uses this enum to validate/restrict the --target option's input.
    example = enum.auto()
    httpbin = enum.auto()
    google = enum.auto()
    allegro = enum.auto()
    amazon = enum.auto()
    chatgpt = enum.auto()
    g2 = enum.auto()
    hyatt = enum.auto()
    instagram = enum.auto()
    lowes = enum.auto()
    nordstrom = enum.auto()
    shein = enum.auto()
    tiktok = enum.auto()
    walmart = enum.auto()

@click.command()
@click.option(
    "--target",
    required=True,
    type=click.Choice(TargetsClick, case_sensitive=False),
    help="Test type choice.",
)
@click.option(
    "--rate",
    required=True,
    type=click.IntRange(1, 50),
    help = "Rate of requests per second. Translates to number of jobs started in a batch every time interval(default: 1 second.)",
)
@click.option(
    "--requests",
    required=True,
    type=click.IntRange(1, 6000),
    help = "Number of requests.",
)
@click.option(
    "--db_filename",
    required=True,
    type = str,
    help = "Database filename."
)
def main(target:str, rate:int, requests:int, db_filename:str):
    asyncio.run(start_test(target.name, rate, requests, db_filename)) #type:ignore

if __name__ == "__main__":
    main()

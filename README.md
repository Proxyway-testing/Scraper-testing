# Scraper test environment

## Installation
Follow these steps to set up the project locally: 
### 1. Prerequisites  
- Python 3.11+ installed on your system. 
- `git` installed.

### 2. Clone the Repository  
`bash git clone https://github.com/your-username/your-repo-name.git` 
`cd your-repo-name`
Create and activate an isolated Python environment:

-   **macOS / Linux:**
    
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
-   **Windows (Command Prompt):**
    ```cmd
    python -m venv .venv
    .venv\Scripts\activate.bat
    ```
-   **Windows (PowerShell):**
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```
Make sure your virtual environment is active, then install the required packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt

```
## Usage
This tool is run as a Python module via the command line, using [Click](https://click.palletsprojects.com/) to parse arguments.

### Command  
```bash 
python -m scraper_test --target <TARGET> --rate <RATE> --requests <REQUESTS> --db_filename <DB_FILENAME>
```
### Options

| Option | Required | Type | Description | 
|--|--|--|--| 
|`--target` | Yes | choice | The target to test against. See Available Targets below. |
|`--rate` |Yes | integer (1–50) |Number of requests per second. This translates to the number of jobs started in a batch every time interval (default interval: 1 second). |
|`--requests` | Yes | integer (1–6000) | Total number of requests to send. |
| `--db_filename` | Yes | string | Filename of the database where results will be stored. |

### Concurrency management

The test environment manages the concurrency based on the `--rate`

### Adding a new target

Targets are defined in one place, `scraper_setup()` in `__main__.py`:
```python
case "my_new_target":
    url_file = "urls/my_new_target.txt"
    selector = "div.product-title"   # CSS selector confirming a successful scrape
    scraper = MyCustomScraper(timeout=TIMEOUT, selector=selector)
```
To add a target:
1.  Add a URL list file under `urls/`.
2.  Implement (or copy/adapt from `scraper_templates.py`) the scraper class to use.
3.  Add a `case` for it in `scraper_setup()` with the file path, selector, and scraper instance.
4.  Add the same name to the `TargetsClick` enum so it's accepted by `--target`.

### Test run logic
1. CLI options parsed (target, rate, requests, db_filename)
2. scraper_setup: resolves target to URL file + scraper class
3. URLLoader loads URLs into memory, cycles through them indefinitely and yields one at a time.
4. RequestsController started with batch_size = rate
5. requests URLs submitted to the controller
6. Controller batches + rate-limits calls to scraper.do_request()
7. Each result written to SQLite via SQLWriter
8. Controller stopped once all submissions are drained

-   If `--requests` exceeds the number of URLs in the target's file, URLs are reused from the start (`URLLoader` cycles indefinitely).
-   The database connection is held open for the full run and closed automatically at the end.

## Scraper Template

### Purpose
This module `scraper_templates.py` holds the scraper **implementation classes** — the logic that defines how a request to a specific target/API is made and how its response is parsed. It is the single place in the project meant for custom, per-scraper or target code. A class instance is assigned to a target in the `scraper_setup()` function of __\_\_main\_\___().

### Scraper Template Elements
Every scraper class in this file follows the same shape, so they stay interchangeable wherever the project dispatches to a scraper instance:

-   **`__init__(self, timeout, selector)`** — stores the shared `timeout` (seconds, passed to the HTTP client) and `selector` (CSS selector string checked against the parsed response) for use during the request. Any API keys, base URLs, or fixed headers specific to that target are also set here.
    
-   **`__str__`** — returns `self.name`, a short identifier for logging/debugging.
    
-   **`async def do_request(self, url: str) -> dict`** — performs the HTTP call for `url` and returns a result dict with a fixed set of keys:

| Key | Type | Description |
| -- | -- | --|
| `ts` |`str` | Request start time. ISO 8601 format: YYYY-MM-DDThh:mm:ss |
| `url` | `str` | The requested URL |
| `status` |`int` | HTTP status code |
| `response_time` |`float` | Elapsed seconds for the request |
| `response_size` | `int` | Response body size in bytes |
| `title` | `str` | Page `<title>` extracted from the response |
| `selector` | `bool` | Whether `self.selector` matched an element in the response |
    
-   **`def parse(self, body: str | bytes) -> tuple[str, bool]`** — takes the raw response body and returns `(title, selector_found)`. This is where response-specific parsing logic (HTML, JSON-wrapped HTML, etc.) goes.
    
Keeping this contract stable is what lets new templates be swapped in (hopefully) without touching code elsewhere in the project.

### Included templates

A couple of templates of common scraper implementation included in the file.
- `scraperExampleTemplatePOST`:
`POST` with JSON body (`url`, `headless`, custom params) + auth header
- `scraperExampleTemplateGET`:
`GET` with query params (`apiKey`, `url`, `render`)
- `scraperExampleTemplateGETURL`:
`GET` where the target URL is embedded directly in the endpoint path (`?url={quote_plus(url)}`)
-`scraperExampleTemplatePROXY`:
Direct `GET` to the target URL, routed through an authenticated HTTP proxy, with redirects followed

`scraperExampleTemplatePOST` includes a fully worked `parse()` (BeautifulSoup title extraction with a regex fallback, plus `select()` for the selector check); the other three leave `parse()` as a stub.

## Output

Results are written to a SQLite database via `SQLWriter`, a small batched writer used as a context manager for the duration of a test run/

The database file is whatever path is passed to `--db_filename`; it's created automatically if it doesn't already exist. 

### Schema Every result is written to a single table, `scrape`:

| Column | Type | Description | 
|---|---|---| 
|`id` | `INTEGER` | Auto-incrementing primary key. | 
| `target` | `TEXT` | Target name (e.g. `example`, `google`) as passed to `--target`. | 
| `scraper` | `TEXT` | Name of the scraper implementation used (`scraper.name` from the imported class. | 
| `ts` | `TIMESTAMP` | Request start time. ISO 8601 format: YYYY-MM-DDThh:mm:ss |
| `status` | `INTEGER` | HTTP status code returned for the request. | 
| `response_time` | `FLOAT` | Request duration in seconds. | 
| `response_size` | `INTEGER` | Response body size in bytes. |
| `selector` | `BOOLEAN` | Whether the configured CSS selector was found in the response (scrape "success" check). | 
| `title` | `TEXT` | Page `<title>` extracted from the response. |
| `url` | `TEXT` | The specific URL that was requested. |

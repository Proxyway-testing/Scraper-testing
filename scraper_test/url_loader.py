import itertools
from typing import AsyncIterator, Iterator

class URLLoader:
    def __init__(self, filepath: str):
        self.filepath = filepath

        # Read the file synchronously, once, when instanced.
        with open(self.filepath, "r") as f:
            self.urls = [
                line.strip() for line in f 
                if line.strip() and not line.strip().startswith("#")
            ]
            if not self.urls:
                raise ValueError("URL file is empty.")

    def __iter__(self) -> Iterator[str]:
        """Loops through list of urls while keeping all URLs in memory."""
        return itertools.cycle(self.urls)
        
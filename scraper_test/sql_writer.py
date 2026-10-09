import sqlite3
from pathlib import Path
from typing import Iterable, Sequence, Any

class SQLWriter:
    """Batched SQLite writer"""

    SCHEMA = """
        CREATE TABLE IF NOT EXISTS scrape (
            id INTEGER PRIMARY KEY,
            target TEXT,
            scraper TEXT,
            ts TIMESTAMP,
            status INTEGER,
            response_time FLOAT,
            response_size INTEGER,
            selector BOOLEAN,
            title TEXT,
            url TEXT
        )
    """
    INSERT_SQL = "INSERT INTO scrape (target, scraper, ts, status, response_time, response_size, selector, title, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"

    def __init__(self, path: str|Path, batch_size: int=100):
        self.path = Path(path)
        self.batch_size = batch_size
        self._buffer: list[Sequence[Any]] = []
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(self.SCHEMA)
        self._conn.commit()

    def add(self, target: str, scraper: str, ts: str, status: int, response_time: float | None, response_size: int | None, title: str | None, url: str, selector: bool = False, ) -> None:
        self._buffer.append((target, scraper, ts, status, response_time, response_size, selector, title, url))
        if len(self._buffer) >= self.batch_size:
            self.flush()

    def add_many(self, rows: Iterable[Sequence[Any]]) -> None:
        for row in rows:
            self._buffer.append(row)
            if len(self._buffer) >= self.batch_size:
                self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        with self._conn:
            self._conn.executemany(self.INSERT_SQL, self._buffer)
            self._buffer.clear()

    def close(self) -> None:
        try:
            self.flush()
        finally:
            self._conn.close()

    def __enter__(self) -> "SQLWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


"""Persistent state (SQLite): survives restarts, crashes and redeploys."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass


@dataclass
class Fill:
    ts: float
    market: str
    side: str
    qty: float
    price: float
    fee: float
    tds: float
    order_id: str
    mode: str      # paper | live
    reason: str


SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS fills (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, market TEXT, side TEXT, qty REAL, price REAL,
    fee REAL, tds REAL, order_id TEXT, mode TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS equity (
    ts REAL, market TEXT, mode TEXT, equity REAL, cash REAL, qty REAL, price REAL, target REAL);
CREATE TABLE IF NOT EXISTS events (ts REAL, level TEXT, message TEXT);
"""


class StateStore:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def get(self, key: str, default=None):
        row = self.conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value) -> None:
        self.conn.execute("INSERT INTO kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          (key, json.dumps(value, default=str)))

    def add_fill(self, f: Fill) -> None:
        d = asdict(f)
        self.conn.execute(f"INSERT INTO fills({','.join(d)}) VALUES({','.join('?' * len(d))})", tuple(d.values()))

    def fills(self, market: str | None = None, limit: int = 50) -> list[dict]:
        q, args = "SELECT * FROM fills", ()
        if market:
            q, args = q + " WHERE market=?", (market,)
        cur = self.conn.execute(q + " ORDER BY id DESC LIMIT ?", (*args, limit))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def add_equity(self, market: str, mode: str, equity: float, cash: float, qty: float, price: float,
                   target: float) -> None:
        self.conn.execute("INSERT INTO equity VALUES(?,?,?,?,?,?,?,?)",
                          (time.time(), market, mode, equity, cash, qty, price, target))

    def equity_history(self, market: str, mode: str, limit: int = 1000) -> list[tuple]:
        return self.conn.execute(
            "SELECT ts, equity FROM equity WHERE market=? AND mode=? ORDER BY ts DESC LIMIT ?",
            (market, mode, limit)).fetchall()[::-1]

    def event(self, level: str, message: str) -> None:
        self.conn.execute("INSERT INTO events VALUES(?,?,?)", (time.time(), level, message))

    def events(self, limit: int = 20) -> list[tuple]:
        return self.conn.execute("SELECT ts, level, message FROM events ORDER BY ts DESC LIMIT ?",
                                 (limit,)).fetchall()

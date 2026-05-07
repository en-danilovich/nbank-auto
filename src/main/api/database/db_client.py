from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, Optional, Tuple, Type, TypeVar

import psycopg
from psycopg.rows import dict_row

from src.main.api.configs.config import Config

T = TypeVar("T")


class RequestType(str, Enum):
    SELECT = "SELECT"


def _dsn() -> str:
    """
    Build Postgres DSN from resources/config.properties (with ENV override via Config.get()).
    """
    host = str(Config.get("DB_HOST", "localhost"))
    port = int(Config.get("DB_PORT", 5433))
    dbname = str(Config.get("DB_NAME", "nbank"))
    user = str(Config.get("DB_USERNAME", "postgres"))
    password = str(Config.get("DB_PASSWORD", "postgres"))
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


@contextmanager
def db_conn() -> Generator[psycopg.Connection, None, None]:
    conn = psycopg.connect(_dsn(), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def fetch_one(sql: str, params: Optional[tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return dict(row) if row is not None else None


@dataclass(frozen=True)
class Condition:
    """
    Simple WHERE condition builder for SQL queries.
    Supports equality and AND-chaining (enough for our test checks).
    """

    sql: str
    params: Tuple[Any, ...]

    @staticmethod
    def equal_to(column: str, value: Any) -> "Condition":
        return Condition(sql=f"{column} = %s", params=(value,))

    @staticmethod
    def and_(*conditions: "Condition") -> "Condition":
        conds = [c for c in conditions if c is not None]
        if not conds:
            raise ValueError("At least one condition is required")
        sql = " AND ".join(f"({c.sql})" for c in conds) # (a = %s) AND (b = %s)
        params: Tuple[Any, ...] = tuple(p for c in conds for p in c.params) # ("alex") (1, ) -> ("alex", 1)
        return Condition(sql=sql, params=params)


class DBRequest:
    @staticmethod
    def builder() -> "DBRequestBuilder":
        return DBRequestBuilder()


class DBRequestBuilder:
    def __init__(self):
        self._request_type: Optional[RequestType] = None
        self._table: Optional[str] = None
        self._where: Optional[Condition] = None

    def request_type(self, request_type: RequestType) -> "DBRequestBuilder":
        self._request_type = request_type
        return self

    def table(self, table: str) -> "DBRequestBuilder":
        self._table = table
        return self

    def where(self, condition: Condition) -> "DBRequestBuilder":
        self._where = condition
        return self

    def extract_as(self, dao_cls: Type[T]) -> T:
        if self._request_type != RequestType.SELECT:
            raise NotImplementedError(f"Request type not supported: {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"SELECT * FROM {self._table}"
        params: tuple[Any, ...] = ()
        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params
        sql += " LIMIT 1"

        row = fetch_one(sql, params)
        if row is None:
            raise AssertionError(f"DB row not found. SQL={sql}, params={params}")

        return dao_cls(**row)  # type: ignore[arg-type]

    def extract_optional_as(self, dao_cls: Type[T]) -> Optional[T]:
        if self._request_type != RequestType.SELECT:
            raise NotImplementedError(f"Request type not supported: {self._request_type}")
        if not self._table:
            raise ValueError("Table is required")

        sql = f"SELECT * FROM {self._table}"
        params: tuple[Any, ...] = ()
        if self._where:
            sql += f" WHERE {self._where.sql}"
            params = self._where.params
        sql += " LIMIT 1"

        row = fetch_one(sql, params)
        if row is None:
            return None
        return dao_cls(**row)  # type: ignore[arg-type]
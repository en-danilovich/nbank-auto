from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserDao:
    """
    Representation of a row in 'customers' table.
    Field names are expected to match DB columns (snake_case).
    """

    id: int
    username: str
    password: str
    name: Optional[str]
    role: str
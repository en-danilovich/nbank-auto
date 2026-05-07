from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AccountDao:
    """
    Representation of a row in 'accounts' table.
    Field names are expected to match DB columns (snake_case).
    """

    id: int
    account_number: str
    balance: float
from typing import Any, List

from pydantic import Field

from src.main.api.models.base_model import BaseModel


class AccountDepositResponse(BaseModel):
    id: int
    accountNumber: str
    balance: float
    transactions: List[Any] = Field(default_factory=list)

from typing import List, Dict, Any

from pydantic import Field

from src.main.api.models.base_model import BaseModel


class GetCustomerAccount(BaseModel):
    id: int
    accountNumber: str
    balance: float
    transactions: List[Dict[str, Any]] = Field(default_factory=list)

class GetCustomerProfileResponse(BaseModel):
    id: int
    username: str
    password: str
    name: str | None
    role: str
    accounts: List[GetCustomerAccount]



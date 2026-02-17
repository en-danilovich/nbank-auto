from typing import Dict, List, Any

from src.main.api.models.base_model import BaseModel


class AccountDepositResponse(BaseModel):
    id: int
    accountNumber: str
    balance: float
    transactions: List[Dict[str, Any]]
from typing import Annotated

from src.main.api.generators.generating_rule import MinMaxFloatGeneratingRule
from src.main.api.models.base_model import BaseModel


class AccountDepositRequest(BaseModel):
    accountId: int
    amount: Annotated[float | None | str, MinMaxFloatGeneratingRule(min=0.01, max=5000)]

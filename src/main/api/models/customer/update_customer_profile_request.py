from typing import Annotated

from src.main.api.generators.generating_rule import RegexGeneratingRule
from src.main.api.models.base_model import BaseModel


class UpdateCustomerProfileRequest(BaseModel):
    name: Annotated[str, RegexGeneratingRule(regex=r'^[A-Za-z]{2,15} [A-Za-z]{2,15}$')]

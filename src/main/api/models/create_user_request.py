from typing import Annotated

from src.main.api.models.base_model import BaseModel
from src.main.api.generators.generating_rule import RegexGeneratingRule


class CreateUserRequest(BaseModel):
    username: Annotated[str, RegexGeneratingRule(regex=r"^[A-Za-z0-9]{3,15}$")]
    password: Annotated[str, RegexGeneratingRule(regex=r"^[A-Z]{3}[a-z]{4}[0-9]{3}[$%&]{2}$")]
    role: Annotated[str, RegexGeneratingRule(regex=r"^USER$")]

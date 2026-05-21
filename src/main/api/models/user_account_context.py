from typing import List

from src.main.api.models.base_model import BaseModel
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest


class UserAccountContext(BaseModel):
    user: CreateUserRequest
    accounts: List[CreateAccountResponse]

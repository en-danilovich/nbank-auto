from dataclasses import dataclass
from typing import List, Optional

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest


@dataclass
class PreparedUserAccount:
    user: CreateUserRequest
    account: CreateAccountResponse


@pytest.fixture(scope="function")
def prepared_users(request: pytest.FixtureRequest, api_manager: ApiManager) -> List[CreateUserRequest]:
    marker = request.node.get_closest_marker("prepare_users")
    number = int(marker.kwargs.get("number", 1)) if marker else 1

    users: List[CreateUserRequest] = []
    for _ in range(number):
        user_data: CreateUserRequest = RandomModelGenerator.generate(CreateUserRequest)
        api_manager.admin_steps.create_user(user_data)
        users.append(user_data)
    return users


@pytest.fixture(scope="function")
def prepared_user_accounts(
    request: pytest.FixtureRequest,
    api_manager: ApiManager,
    prepared_users: List[CreateUserRequest],
) -> List[PreparedUserAccount]:
    marker = request.node.get_closest_marker("prepare_accounts")
    number = int(marker.kwargs.get("number", 1)) if marker else 1
    deposit: Optional[float] = None
    if marker is not None and "deposit" in marker.kwargs:
        deposit = float(marker.kwargs["deposit"])

    if not prepared_users:
        return []

    result: List[PreparedUserAccount] = []
    users_count = len(prepared_users)
    for i in range(number):
        user = prepared_users[i % users_count]
        account: CreateAccountResponse = api_manager.user_steps.create_account(user)

        if deposit is not None:
            api_manager.user_steps.deposit_money_to_account(user, account.id, float(deposit))

        result.append(PreparedUserAccount(user=user, account=account))
    return result

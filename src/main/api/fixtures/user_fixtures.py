from typing import List

import pytest

from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.user_account_context import UserAccountContext


@pytest.fixture(scope='function')
def user_request(api_manager: ApiManager):
    user_data: CreateUserRequest = RandomModelGenerator.generate(CreateUserRequest)
    api_manager.admin_steps.create_user(user_data)
    return user_data


@pytest.fixture
def admin_user_request():
    return CreateUserRequest(username='admin', password='admin', role='ADMIN')


@pytest.fixture(scope='function')
def account_data(api_manager: ApiManager, user_request: CreateUserRequest):
    return api_manager.user_steps.create_account(user_request)


@pytest.fixture(scope='function')
def users(request, api_manager: ApiManager) -> List[CreateUserRequest]:
    marker = request.node.get_closest_marker("with_users")
    config = marker.kwargs if marker else {}
    count = config.get("count", 1)

    created_users = []

    for _ in range(count):
        user_data = RandomModelGenerator.generate(CreateUserRequest)
        api_manager.admin_steps.create_user(user_data)

        created_users.append(user_data)

    return created_users

@pytest.fixture
def accounts_with_balance(request, users, api_manager) -> List[UserAccountContext]:
    marker = request.node.get_closest_marker("with_users")
    config = marker.kwargs if marker else {}
    accounts_count = config.get("accounts_count", 1)
    balance = config.get("balance", None)

    context_list: List[UserAccountContext] = []
    for user_data in users:
        user_accounts = []
        for _ in range(accounts_count):
            account_data: CreateAccountResponse = api_manager.user_steps.create_account(user_data)
            if balance is not None:
                deposit_balance(api_manager, user_data, account_data.id, balance)
                account_data.balance = balance
            user_accounts.append(account_data)
        context_list.append(UserAccountContext(user=user_data, accounts=user_accounts))

    return context_list

def deposit_balance(api_manager: ApiManager, create_user_request: CreateUserRequest,
                    account_id: int, balance: float, max_deposit: float = 5000):
    remaining_sum = balance

    while remaining_sum > 0:
        # Берем либо 5000, либо остаток, если он меньше 5000
        deposit_amount = min(remaining_sum, max_deposit)
        api_manager.user_steps.deposit_money_to_account(create_user_request, account_id, deposit_amount)

        remaining_sum -= deposit_amount

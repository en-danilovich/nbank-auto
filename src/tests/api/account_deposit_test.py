import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.accounts.account_deposit_request import AccountDepositRequest
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


@pytest.mark.api
class TestAccountDeposit(BaseTest):
    def test_account_deposit_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.ACCOUNTS_DEPOSIT,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    @pytest.mark.parametrize('balance', [
        "",
        None
    ])
    def test_account_deposit_empty_balance(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                           account_data: CreateAccountResponse, balance: str | None):
        api_manager.user_steps.deposit_money_with_empty_balance(user_request, account_data.id, balance)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, account_data.balance)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    @pytest.mark.parametrize('balance', [
        0.01,
        RandomData.get_deposit_balance(),
        5000.00,
    ])
    def test_account_deposit(self, api_manager: ApiManager, user_request: CreateUserRequest,
                             account_data: CreateAccountResponse, balance: float):
        api_manager.user_steps.deposit_money_to_account(user_request, account_data.id, balance, 0.00)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, balance)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    def test_account_deposit_multiple_deposits(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                               account_data: CreateAccountResponse):
        deposit_balance = RandomData.get_deposit_balance()
        api_manager.user_steps.deposit_money_to_account(user_request, account_data.id, deposit_balance, 0.00)
        current_balance = deposit_balance

        next_deposit = RandomData.get_deposit_balance()
        api_manager.user_steps.deposit_money_to_account(user_request, account_data.id, next_deposit, current_balance)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, deposit_balance + next_deposit)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    def test_account_deposit_two_same_deposits_in_a_row(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                                        account_data: CreateAccountResponse):
        deposit_balance = RandomData.get_deposit_balance()
        api_manager.user_steps.deposit_money_to_account(user_request, account_data.id, deposit_balance, 0.00)
        api_manager.user_steps.deposit_money_to_account(user_request, account_data.id, deposit_balance, deposit_balance)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, deposit_balance * 2)

    @pytest.mark.usefixtures('user_request', 'api_manager')
    def test_account_deposit_account_belonging_to_another_user(self, api_manager: ApiManager, user_request: CreateUserRequest):
        second_user_request: CreateUserRequest = RandomModelGenerator.generate(CreateUserRequest)
        api_manager.admin_steps.create_user(second_user_request)
        second_user_account_response: CreateAccountResponse = api_manager.user_steps.create_account(second_user_request)

        api_manager.user_steps.deposit_money_to_invalid_account(user_request, second_user_account_response.id)
        api_manager.user_steps.verify_account_balance(second_user_request, second_user_account_response.id, second_user_account_response.balance)

    @pytest.mark.usefixtures('api_manager', 'user_request')
    def test_account_deposit_nonexisting_account(self, api_manager: ApiManager, user_request: CreateUserRequest):
        api_manager.user_steps.deposit_money_to_invalid_account(user_request,
                                                                RandomModelGenerator.generate(AccountDepositRequest).id)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    @pytest.mark.parametrize('balance, error_message', [
        (-0.01, "Invalid account or amount"),
        (0.00, "Invalid account or amount"),
        (5000.01, "Deposit amount cannot exceed 5000"),
    ])
    def test_account_deposit_invalid_deposit_balance(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                             account_data: CreateAccountResponse, balance: float | None, error_message: str):
        api_manager.user_steps.deposit_money_with_invalid_balance(user_request, account_data.id, balance, error_message)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, account_data.balance)



from typing import List

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.fixtures.prepare_data_fixtures import PreparedUserAccount
from src.main.api.generators.random_data import RandomData
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.accounts.account_deposit_request import AccountDepositRequest
from src.main.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


@pytest.mark.api
@pytest.mark.api_version("with_database")
class TestAccountDeposit(BaseTest):
    def test_account_deposit_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.ACCOUNTS_DEPOSIT,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    @pytest.mark.parametrize('balance', [
        "",
        None
    ])
    def test_account_deposit_empty_balance(self, api_manager: ApiManager,
                                           prepared_user_accounts: List[PreparedUserAccount],
                                           balance: str | None):
        owner = prepared_user_accounts[0]
        api_manager.user_steps.deposit_money_with_empty_balance(owner.user, owner.account.id, balance)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, owner.account.balance)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        assert account_dao.balance == owner.account.balance, (
            f"DB balance changed after empty-balance deposit: expected {owner.account.balance}, got {account_dao.balance}"
        )

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    @pytest.mark.parametrize('balance', [
        0.01,
        RandomData.get_deposit_balance(),
        5000.00,
    ])
    def test_account_deposit(self, api_manager: ApiManager,
                             prepared_user_accounts: List[PreparedUserAccount],
                             balance: float):
        owner = prepared_user_accounts[0]
        deposit_response = api_manager.user_steps.deposit_money_to_account(owner.user, owner.account.id, balance, 0.00)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, balance)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        DaoAndModelAssertions.assert_that(deposit_response, account_dao).match()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    def test_account_deposit_multiple_deposits(self, api_manager: ApiManager,
                                               prepared_user_accounts: List[PreparedUserAccount]):
        owner = prepared_user_accounts[0]
        deposit_balance = RandomData.get_deposit_balance()
        api_manager.user_steps.deposit_money_to_account(owner.user, owner.account.id, deposit_balance, 0.00)
        current_balance = deposit_balance

        next_deposit = RandomData.get_deposit_balance()
        deposit_response = api_manager.user_steps.deposit_money_to_account(owner.user, owner.account.id, next_deposit, current_balance)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, deposit_balance + next_deposit)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        DaoAndModelAssertions.assert_that(deposit_response, account_dao).match()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    def test_account_deposit_two_same_deposits_in_a_row(self, api_manager: ApiManager,
                                                        prepared_user_accounts: List[PreparedUserAccount]):
        owner = prepared_user_accounts[0]
        deposit_balance = RandomData.get_deposit_balance()
        api_manager.user_steps.deposit_money_to_account(owner.user, owner.account.id, deposit_balance, 0.00)
        deposit_response = api_manager.user_steps.deposit_money_to_account(owner.user, owner.account.id, deposit_balance, deposit_balance)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, deposit_balance * 2)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        DaoAndModelAssertions.assert_that(deposit_response, account_dao).match()

    @pytest.mark.prepare_users(number=2)
    @pytest.mark.prepare_accounts(number=1)
    def test_account_deposit_account_belonging_to_another_user(self, api_manager: ApiManager,
                                                               prepared_users,
                                                               prepared_user_accounts: List[PreparedUserAccount]):
        owner = prepared_user_accounts[0]
        intruder = prepared_users[1]

        api_manager.user_steps.deposit_money_to_invalid_account(intruder, owner.account.id)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, owner.account.balance)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        assert account_dao.balance == owner.account.balance, (
            f"DB balance changed after forbidden deposit: expected {owner.account.balance}, got {account_dao.balance}"
        )

    @pytest.mark.prepare_users(number=1)
    def test_account_deposit_nonexisting_account(self, api_manager: ApiManager, prepared_users):
        api_manager.user_steps.deposit_money_to_invalid_account(prepared_users[0],
                                                                RandomModelGenerator.generate(AccountDepositRequest).accountId)

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    @pytest.mark.parametrize('balance, error_message', [
        (-0.01, "Invalid account or amount"),
        (0.00, "Invalid account or amount"),
        (5000.01, "Deposit amount exceeds the 5000 limit"),
    ])
    def test_account_deposit_invalid_deposit_balance(self, api_manager: ApiManager,
                                                     prepared_user_accounts: List[PreparedUserAccount],
                                                     balance: float | None, error_message: str):
        owner = prepared_user_accounts[0]
        api_manager.user_steps.deposit_money_with_invalid_balance(owner.user, owner.account.id, balance, error_message)
        api_manager.user_steps.verify_account_balance(owner.user, owner.account.id, owner.account.balance)

        account_dao = api_manager.database_steps.get_account_by_account_number(owner.account.accountNumber)
        assert account_dao.balance == owner.account.balance, (
            f"DB balance changed after invalid deposit: expected {owner.account.balance}, got {account_dao.balance}"
        )

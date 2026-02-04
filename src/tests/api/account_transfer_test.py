from typing import List

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_transfer_request import AccountTransferRequest
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.user_account_context import UserAccountContext
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


class TestAccountTransfer(BaseTest):
    def test_account_transfer_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.ACCOUNTS_DEPOSIT,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.with_users(accounts_count=2, balance=10000)
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('transfer_amount', [
        0.01,
        RandomData.get_deposit_balance(),
        10000.0,
    ])
    def test_account_transfer_to_owned_account(self, accounts_with_balance: List[UserAccountContext],
                                               api_manager: ApiManager,
                                               transfer_amount: float):
        user_context = accounts_with_balance[0]
        transfer_request = AccountTransferRequest(senderAccountId=user_context.accounts[0].id,
                                                  receiverAccountId=user_context.accounts[1].id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account(user_context.user, transfer_request)

    @pytest.mark.with_users(count=2, accounts_count=1, balance=5000)
    @pytest.mark.usefixtures('api_manager')
    def test_account_transfer_to_another_user_account(self, accounts_with_balance: List[UserAccountContext],
                                                      api_manager: ApiManager):
        sender_user_context = accounts_with_balance[0]
        receiver_user_context = accounts_with_balance[1]

        transfer_request = AccountTransferRequest(senderAccountId=sender_user_context.accounts[0].id,
                                                  receiverAccountId=receiver_user_context.accounts[0].id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account(sender_user_request=sender_user_context.user,
                                                         transfer_request=transfer_request,
                                                         receiver_user_request=receiver_user_context.user)

    @pytest.mark.with_users(accounts_count=2, balance=10000)
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('transfer_amount, error_message', [
        (-0.01, 'Transfer amount must be at least 0.01'),
        (0, 'Transfer amount must be at least 0.01'),
        (10000.1, 'Transfer amount cannot exceed 10000'),
    ])
    def test_account_transfer_invalid_transfer_amount(self, accounts_with_balance: List[UserAccountContext],
                                                      api_manager: ApiManager,
                                                      transfer_amount: float,
                                                      error_message: str):
        user_context = accounts_with_balance[0]
        transfer_request = AccountTransferRequest(senderAccountId=user_context.accounts[0].id,
                                                  receiverAccountId=user_context.accounts[1].id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_context.user, transfer_request, error_message)

    @pytest.mark.with_users(accounts_count=2)
    @pytest.mark.usefixtures('api_manager')
    def test_account_transfer_insufficent_funds(self, accounts_with_balance: List[UserAccountContext], api_manager: ApiManager):
        user_context = accounts_with_balance[0]
        transfer_request = AccountTransferRequest(senderAccountId=user_context.accounts[0].id,
                                                  receiverAccountId=user_context.accounts[1].id,
                                                  amount=RandomData.get_deposit_balance())
        error_message = "Invalid transfer: insufficient funds or invalid accounts"
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_context.user, transfer_request, error_message)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    @pytest.mark.parametrize('random_receiver_account', [
        True,
        False,
    ])
    def test_account_transfer_invalid_sender_account_id(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                                        account_data: CreateAccountResponse,
                                                        random_receiver_account: bool):
        """
        covered 2 cases
            1. transfer non existing sender account_id
            2. receiver and sender account ids are the same
        """

        transfer_request = AccountTransferRequest(
            senderAccountId=account_data.id,
            receiverAccountId=RandomData.get_invalid_account_id() if random_receiver_account else account_data.id,
            amount=RandomData.get_deposit_balance())
        error_message = "Invalid transfer: insufficient funds or invalid accounts"
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_request, transfer_request, error_message)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    def test_account_transfer_non_existing_receiver_account_id(self, api_manager: ApiManager,
                                                               user_request: CreateUserRequest,
                                                               account_data: CreateAccountResponse):
        transfer_request = AccountTransferRequest(
            senderAccountId=RandomData.get_invalid_account_id(),
            receiverAccountId=account_data.id,
            amount=RandomData.get_deposit_balance())

        api_manager.user_steps.transfer_money_to_account_forbidden_action(user_request, transfer_request)

    @pytest.mark.with_users(count=2)
    @pytest.mark.usefixtures('api_manager')
    def test_account_transfer_user_has_no_access_to_other_user_account(self, accounts_with_balance: List[UserAccountContext], api_manager: ApiManager):
        first_user_context = accounts_with_balance[0]
        second_user_context = accounts_with_balance[1]
        transfer_request = AccountTransferRequest(senderAccountId=first_user_context.accounts[0].id,
                                                  receiverAccountId=second_user_context.accounts[0].id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_forbidden_action(second_user_context.user, transfer_request)

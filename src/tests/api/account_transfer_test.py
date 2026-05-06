from typing import List

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.constants.error_messages import ErrorMessages
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
            endpoint=Endpoint.ACCOUNTS_TRANSFER,
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
        sender_account, receiver_account = user_context.accounts[0], user_context.accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=sender_account.id,
                                                  receiverAccountId=receiver_account.id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account(user_context.user, transfer_request)

        api_manager.user_steps.verify_account_balance(user_context.user, sender_account.id,
                                                      sender_account.balance - transfer_amount)
        api_manager.user_steps.verify_account_balance(user_context.user, receiver_account.id,
                                                      receiver_account.balance + transfer_amount)


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
                                                         transfer_request=transfer_request)

        api_manager.user_steps.verify_account_balance(sender_user_context.user, sender_user_context.accounts[0].id,
                                                      sender_user_context.accounts[0].balance - transfer_request.amount)
        api_manager.user_steps.verify_account_balance(receiver_user_context.user, receiver_user_context.accounts[0].id,
                                                      receiver_user_context.accounts[0].balance + transfer_request.amount)

    @pytest.mark.with_users(accounts_count=2, balance=15000)
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('transfer_amount, error_message', [
        (-0.01, ErrorMessages.INVALID_TRANSFER),
        (0, ErrorMessages.INVALID_TRANSFER),
        (10000.1, ErrorMessages.INVALID_TRANSFER),
    ])
    def test_account_transfer_invalid_transfer_amount(self, accounts_with_balance: List[UserAccountContext],
                                                      api_manager: ApiManager,
                                                      transfer_amount: float,
                                                      error_message: str):
        user_context = accounts_with_balance[0]
        first_account, second_account = user_context.accounts[0], user_context.accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=first_account.id,
                                                  receiverAccountId=second_account.id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_context.user, transfer_request, error_message)
        api_manager.user_steps.verify_account_balance(user_context.user, first_account.id, first_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, second_account.id, second_account.balance)

    @pytest.mark.with_users(accounts_count=2)
    @pytest.mark.usefixtures('api_manager')
    def test_account_transfer_insufficent_funds(self, accounts_with_balance: List[UserAccountContext], api_manager: ApiManager):
        user_context = accounts_with_balance[0]
        first_account, second_account = user_context.accounts[0], user_context.accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=user_context.accounts[0].id,
                                                  receiverAccountId=user_context.accounts[1].id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_context.user, transfer_request,
                                                                      ErrorMessages.INVALID_TRANSFER)
        api_manager.user_steps.verify_account_balance(user_context.user, first_account.id, first_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, second_account.id, second_account.balance)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    @pytest.mark.parametrize('random_receiver_account', [
        True,
        False,
    ])
    def test_account_transfer_invalid_receiver_account_id(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                                        account_data: CreateAccountResponse,
                                                        random_receiver_account: bool):
        """
        covered 2 cases
            1. transfer non existing receiver account_id
            2. receiver and sender account ids are the same
        """

        transfer_request = AccountTransferRequest(
            senderAccountId=account_data.id,
            receiverAccountId=RandomData.get_invalid_account_id() if random_receiver_account else account_data.id,
            amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_invalid_data(user_request, transfer_request,
                                                                      ErrorMessages.INVALID_TRANSFER)
        if not random_receiver_account:
            api_manager.user_steps.verify_account_balance(user_request, account_data.id, account_data.balance)

    @pytest.mark.usefixtures('api_manager', 'user_request', 'account_data')
    def test_account_transfer_non_existing_sender_account_id(self, api_manager: ApiManager,
                                                             user_request: CreateUserRequest,
                                                             account_data: CreateAccountResponse):
        transfer_request = AccountTransferRequest(
            senderAccountId=RandomData.get_invalid_account_id(),
            receiverAccountId=account_data.id,
            amount=RandomData.get_deposit_balance())

        api_manager.user_steps.transfer_money_to_account_forbidden_action(user_request, transfer_request)
        api_manager.user_steps.verify_account_balance(user_request, account_data.id, account_data.balance)

    @pytest.mark.with_users(count=2)
    @pytest.mark.usefixtures('api_manager')
    def test_account_transfer_user_has_no_access_to_other_user_account(self, accounts_with_balance: List[UserAccountContext], api_manager: ApiManager):
        first_user_context = accounts_with_balance[0]
        second_user_context = accounts_with_balance[1]
        transfer_request = AccountTransferRequest(senderAccountId=first_user_context.accounts[0].id,
                                                  receiverAccountId=second_user_context.accounts[0].id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_forbidden_action(second_user_context.user, transfer_request)
        api_manager.user_steps.verify_account_balance(first_user_context.user,
                                                      first_user_context.accounts[0].id,
                                                      first_user_context.accounts[0].balance)
        api_manager.user_steps.verify_account_balance(second_user_context.user,
                                                      second_user_context.accounts[0].id,
                                                      second_user_context.accounts[0].balance)

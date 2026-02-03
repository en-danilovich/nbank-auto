from typing import List

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_transfer_request import AccountTransferRequest
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
    def test_account_transfer(self, accounts_with_balance: List[UserAccountContext],
                              api_manager: ApiManager,
                              transfer_amount: float):
        user_context = accounts_with_balance[0]
        transfer_request = AccountTransferRequest(senderAccountId=user_context.accounts[0].id,
                                                  receiverAccountId=user_context.accounts[1].id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account(user_context.user, transfer_request)
        #TODO: verify account current balance

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
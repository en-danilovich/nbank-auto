from typing import List

import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.constants.error_messages import ErrorMessages
from src.main.api.fixtures.prepare_data_fixtures import PreparedUserAccount
from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_transfer_request import AccountTransferRequest
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


@pytest.mark.api_version("with_database")
class TestAccountTransfer(BaseTest):
    def test_account_transfer_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.ACCOUNTS_TRANSFER,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=2, deposit=10000)
    @pytest.mark.parametrize('transfer_amount', [
        0.01,
        RandomData.get_deposit_balance(),
        10000.0,
    ])
    def test_account_transfer_to_owned_account(self, api_manager: ApiManager,
                                               prepared_user_accounts: List[PreparedUserAccount],
                                               transfer_amount: float):
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=sender.account.id,
                                                  receiverAccountId=receiver.account.id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account(sender.user, transfer_request)

        api_manager.user_steps.verify_account_balance(sender.user, sender.account.id,
                                                      sender.account.balance - transfer_amount)
        api_manager.user_steps.verify_account_balance(sender.user, receiver.account.id,
                                                      receiver.account.balance + transfer_amount)

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == round(sender.account.balance - transfer_amount, 2), (
            f"Sender DB balance mismatch: expected {sender.account.balance - transfer_amount}, got {sender_dao.balance}"
        )
        assert receiver_dao.balance == round(receiver.account.balance + transfer_amount, 2), (
            f"Receiver DB balance mismatch: expected {receiver.account.balance + transfer_amount}, got {receiver_dao.balance}"
        )


    @pytest.mark.prepare_users(number=2)
    @pytest.mark.prepare_accounts(number=2, deposit=5000)
    def test_account_transfer_to_another_user_account(self, api_manager: ApiManager,
                                                      prepared_user_accounts: List[PreparedUserAccount]):
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]

        transfer_request = AccountTransferRequest(senderAccountId=sender.account.id,
                                                  receiverAccountId=receiver.account.id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account(sender_user_request=sender.user,
                                                         transfer_request=transfer_request)

        api_manager.user_steps.verify_account_balance(sender.user, sender.account.id,
                                                      sender.account.balance - transfer_request.amount)
        api_manager.user_steps.verify_account_balance(receiver.user, receiver.account.id,
                                                      receiver.account.balance + transfer_request.amount)

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == round(sender.account.balance - transfer_request.amount, 2), (
            f"Sender DB balance mismatch: expected {sender.account.balance - transfer_request.amount}, got {sender_dao.balance}"
        )
        assert receiver_dao.balance == round(receiver.account.balance + transfer_request.amount, 2), (
            f"Receiver DB balance mismatch: expected {receiver.account.balance + transfer_request.amount}, got {receiver_dao.balance}"
        )

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=2, deposit=15000)
    @pytest.mark.parametrize('transfer_amount, error_message', [
        (-0.01, ErrorMessages.INVALID_TRANSFER),
        (0, ErrorMessages.INVALID_TRANSFER),
        (10000.1, ErrorMessages.MAX_TRANSFER_AMOUNT_MSG),
    ])
    def test_account_transfer_invalid_transfer_amount(self, api_manager: ApiManager,
                                                      prepared_user_accounts: List[PreparedUserAccount],
                                                      transfer_amount: float,
                                                      error_message: str):
        first = prepared_user_accounts[0]
        second = prepared_user_accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=first.account.id,
                                                  receiverAccountId=second.account.id,
                                                  amount=transfer_amount)
        api_manager.user_steps.transfer_money_to_account_invalid_data(first.user, transfer_request, error_message)
        api_manager.user_steps.verify_account_balance(first.user, first.account.id, first.account.balance)
        api_manager.user_steps.verify_account_balance(first.user, second.account.id, second.account.balance)

        first_dao = api_manager.database_steps.get_account_by_account_number(first.account.accountNumber)
        second_dao = api_manager.database_steps.get_account_by_account_number(second.account.accountNumber)
        assert first_dao.balance == first.account.balance, f"Sender DB balance changed: {first_dao.balance}"
        assert second_dao.balance == second.account.balance, f"Receiver DB balance changed: {second_dao.balance}"

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=2)
    def test_account_transfer_insufficent_funds(self, api_manager: ApiManager,
                                                prepared_user_accounts: List[PreparedUserAccount]):
        first = prepared_user_accounts[0]
        second = prepared_user_accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=first.account.id,
                                                  receiverAccountId=second.account.id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_invalid_data(first.user, transfer_request,
                                                                      ErrorMessages.INVALID_TRANSFER)
        api_manager.user_steps.verify_account_balance(first.user, first.account.id, first.account.balance)
        api_manager.user_steps.verify_account_balance(first.user, second.account.id, second.account.balance)

        first_dao = api_manager.database_steps.get_account_by_account_number(first.account.accountNumber)
        second_dao = api_manager.database_steps.get_account_by_account_number(second.account.accountNumber)
        assert first_dao.balance == first.account.balance, f"Sender DB balance changed: {first_dao.balance}"
        assert second_dao.balance == second.account.balance, f"Receiver DB balance changed: {second_dao.balance}"

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    @pytest.mark.parametrize('random_receiver_account', [
        True,
        False,
    ])
    def test_account_transfer_invalid_receiver_account_id(self, api_manager: ApiManager,
                                                          prepared_user_accounts: List[PreparedUserAccount],
                                                          random_receiver_account: bool):
        """
        covered 2 cases
            1. transfer non existing receiver account_id
            2. receiver and sender account ids are the same
        """
        sender = prepared_user_accounts[0]

        transfer_request = AccountTransferRequest(
            senderAccountId=sender.account.id,
            receiverAccountId=RandomData.get_invalid_account_id() if random_receiver_account else sender.account.id,
            amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_invalid_data(sender.user, transfer_request,
                                                                      ErrorMessages.INVALID_TRANSFER)
        if not random_receiver_account:
            api_manager.user_steps.verify_account_balance(sender.user, sender.account.id, sender.account.balance)

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        assert sender_dao.balance == sender.account.balance, f"Sender DB balance changed: {sender_dao.balance}"

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.prepare_accounts(number=1)
    def test_account_transfer_non_existing_sender_account_id(self, api_manager: ApiManager,
                                                             prepared_user_accounts: List[PreparedUserAccount]):
        receiver = prepared_user_accounts[0]
        transfer_request = AccountTransferRequest(
            senderAccountId=RandomData.get_invalid_account_id(),
            receiverAccountId=receiver.account.id,
            amount=RandomData.get_deposit_balance())

        api_manager.user_steps.transfer_money_to_account_forbidden_action(receiver.user, transfer_request)
        api_manager.user_steps.verify_account_balance(receiver.user, receiver.account.id, receiver.account.balance)

        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert receiver_dao.balance == receiver.account.balance, f"Receiver DB balance changed: {receiver_dao.balance}"

    @pytest.mark.prepare_users(number=2)
    @pytest.mark.prepare_accounts(number=2)
    def test_account_transfer_user_has_no_access_to_other_user_account(self, api_manager: ApiManager,
                                                                       prepared_user_accounts: List[PreparedUserAccount]):
        first = prepared_user_accounts[0]
        second = prepared_user_accounts[1]
        transfer_request = AccountTransferRequest(senderAccountId=first.account.id,
                                                  receiverAccountId=second.account.id,
                                                  amount=RandomData.get_deposit_balance())
        api_manager.user_steps.transfer_money_to_account_forbidden_action(second.user, transfer_request)
        api_manager.user_steps.verify_account_balance(first.user, first.account.id, first.account.balance)
        api_manager.user_steps.verify_account_balance(second.user, second.account.id, second.account.balance)

        first_dao = api_manager.database_steps.get_account_by_account_number(first.account.accountNumber)
        second_dao = api_manager.database_steps.get_account_by_account_number(second.account.accountNumber)
        assert first_dao.balance == first.account.balance, f"Sender DB balance changed: {first_dao.balance}"
        assert second_dao.balance == second.account.balance, f"Receiver DB balance changed: {second_dao.balance}"

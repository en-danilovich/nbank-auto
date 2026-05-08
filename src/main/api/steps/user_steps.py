from typing import Optional

from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_deposit_request import AccountDepositRequest
from src.main.api.models.accounts.account_deposit_response import AccountDepositResponse
from src.main.api.models.accounts.account_transfer_request import AccountTransferRequest
from src.main.api.models.accounts.account_transfer_response import AccountTransferResponse
from src.main.api.models.accounts.account_transfer_with_fraud_check_request import AccountTransferWithFraudCheckRequest
from src.main.api.models.accounts.account_transfer_with_fraud_check_response import AccountTransferWithFraudCheckResponse
from typing import List

from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.comparison.model_assertions import ModelAssertions
from src.main.api.models.customer.get_customer_profile_response import GetCustomerProfileResponse, GetCustomerAccount
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.models.customer.update_customer_profile_response import UpdateCustomerProfileResponse
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.requests.skeleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.steps.base_steps import BaseSteps
from src.main.api.models.login_user_request import LoginUserRequest
from src.main.api.models.login_user_response import LoginUserResponse
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs


class UserSteps(BaseSteps):
    def login(self, user_request: CreateUserRequest) -> LoginUserResponse:
        login_request = LoginUserRequest(username=user_request.username, password=user_request.password)
        login_response: LoginUserResponse = ValidatedCrudRequester(
            RequestSpecs.unauth_spec(),
            Endpoint.LOGIN_USER,
            ResponseSpecs.request_returns_ok()
        ).post(login_request)
        ModelAssertions(login_request, login_response).match()
        return login_response

    def create_account(self, user_request: CreateUserRequest) -> CreateAccountResponse:
        create_account_response: CreateAccountResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.CREATE_ACCOUNT,
            ResponseSpecs.entity_was_created()
        ).post()

        assert create_account_response.balance == 0.0
        assert not create_account_response.transactions
        return create_account_response

    def deposit_money_to_account(self, user_request: CreateUserRequest, account_id: int, deposit_balance: float,
                                 current_account_balance: Optional[float] = None) -> AccountDepositResponse:
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            accountId=account_id,
            amount=deposit_balance,
        )
        account_deposit_response: AccountDepositResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.request_returns_ok()
        ).post(account_deposit_request)

        ModelAssertions(account_deposit_request, account_deposit_response).match()

        if current_account_balance:
            expected_balance = round(current_account_balance + deposit_balance, 2)
            assert account_deposit_response.balance == expected_balance, (
                f"Expected account balance is incorrect, expected {expected_balance}, but got {account_deposit_response.balance}"
            )

        assert account_deposit_response.depositAmount == account_deposit_request.amount, (
            f"Expected depositAmount {account_deposit_request.amount}, but got {account_deposit_response.depositAmount}"
        )
        assert account_deposit_response.transactionId, (
            f"Expected non-empty transactionId in deposit response, but got {account_deposit_response.transactionId}"
        )

        return account_deposit_response

    def deposit_money_to_invalid_account(self, user_request: CreateUserRequest, account_id: int):
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            accountId=account_id,
            amount=RandomData.get_deposit_balance(),
        )
        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.action_forbidden()
        ).post(account_deposit_request)

    def deposit_money_with_invalid_balance(self, user_request: CreateUserRequest,
                                           account_id: int,
                                           balance: float,
                                           error_message: str):
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            accountId=account_id,
            amount=balance,
        )

        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.request_returns_bad_request_with_text(error_message)
        ).post(account_deposit_request)

    def deposit_money_with_empty_balance(self, user_request: CreateUserRequest, account_id: int, balance: str | None):
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            accountId=account_id,
            amount=balance,
        )

        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.internal_server_error()
        ).post(account_deposit_request)

    def update_profile(self, user_request: CreateUserRequest, update_customer_profile_request: UpdateCustomerProfileRequest) -> UpdateCustomerProfileResponse:
        update_customer_profile_response: UpdateCustomerProfileResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.UPDATE_CUSTOMER_PROFILE,
            ResponseSpecs.request_returns_ok()
        ).update(update_customer_profile_request)

        ModelAssertions(update_customer_profile_response.customer, user_request).match()

        assert update_customer_profile_response.message == "Profile updated successfully"
        assert update_customer_profile_response.customer.name == update_customer_profile_request.name, (
            f"Incorrect '{update_customer_profile_response.customer.username}' customer.name, expected '{update_customer_profile_request.name}'"
        )

        return update_customer_profile_response

    def update_profile_using_invalid_data(self, user_request: CreateUserRequest,
                                          update_customer_profile_request: UpdateCustomerProfileRequest,
                                          error_message: str):
        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.UPDATE_CUSTOMER_PROFILE,
            ResponseSpecs.request_returns_bad_request_with_text(error_message)
        ).update(update_customer_profile_request)

    def transfer_money_to_account(self, sender_user_request: CreateUserRequest, transfer_request: AccountTransferRequest) -> AccountTransferResponse:
        transfer_response: AccountTransferResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(sender_user_request.username, sender_user_request.password),
            Endpoint.ACCOUNTS_TRANSFER,
            ResponseSpecs.request_returns_ok()
        ).post(transfer_request)

        ModelAssertions(transfer_request, transfer_response).match()
        assert transfer_response.message == "Transfer successful"

        return transfer_response

    def transfer_money_to_account_invalid_data(self, user_request: CreateUserRequest,
                                               transfer_request: AccountTransferRequest,
                                               error_message: str):
        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_TRANSFER,
            ResponseSpecs.request_returns_bad_request_with_text(error_message)
        ).post(transfer_request)


    def transfer_money_to_account_forbidden_action(self, user_request: CreateUserRequest, transfer_request: AccountTransferRequest):
        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_TRANSFER,
            ResponseSpecs.action_forbidden()
        ).post(transfer_request)

    def get_profile(self, user_request: CreateUserRequest) -> GetCustomerProfileResponse:
        profile_response: GetCustomerProfileResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.GET_CUSTOMER_PROFILE,
            ResponseSpecs.request_returns_ok()
        ).get()

        return profile_response

    def verify_account_balance(self, user_request: CreateUserRequest, account_id: int, expected_balance: float):
        profile = self.get_profile(user_request)
        account = self._get_account_data_from_profile(profile, account_id)
        expected_balance = round(expected_balance, 2)

        assert expected_balance == account.balance, (
            f"Verify account balance is '{expected_balance}', but got {account.balance}."
            f"\nUsername: '{user_request.username}'\nAccount ID: '{account_id}'"
        )

    def _get_account_data_from_profile(self, profile: GetCustomerProfileResponse, account_id: int) -> Optional[GetCustomerAccount]:
        return next((acc for acc in profile.accounts if acc.id == account_id), None)

    def get_all_accounts(self, user_request: CreateUserRequest) -> List[CreateAccountResponse]:
        user_accounts: List[CreateAccountResponse] = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.GET_CUSTOMER_ACCOUNTS,
            ResponseSpecs.request_returns_ok()
        ).get()

        return user_accounts

    def transfer_with_fraud_check(
        self,
        user_request: CreateUserRequest,
        sender_account_id: int,
        receiver_account_id: int,
        amount: float,
    ) -> AccountTransferWithFraudCheckResponse:
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=sender_account_id,
            receiverAccountId=receiver_account_id,
            amount=amount,
        )
        transfer_response: AccountTransferWithFraudCheckResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_TRANSFER_WITH_FRAUD_CHECK,
            ResponseSpecs.request_returns_ok()
        ).post(transfer_request)
        return transfer_response

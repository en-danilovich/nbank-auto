from typing import Optional

from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_deposit_request import AccountDepositRequest
from src.main.api.models.accounts.account_deposit_response import AccountDepositResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.comparison.model_assertions import ModelAssertions
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
            id=account_id,
            balance=deposit_balance,
        )
        account_deposit_response: AccountDepositResponse = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.request_returns_ok()
        ).post(account_deposit_request)

        ModelAssertions(account_deposit_request, account_deposit_response).match()

        if current_account_balance:
            expected_balance = current_account_balance + deposit_balance
            assert account_deposit_response.balance == expected_balance, (
                f"Expected account balance is incorrect, expected {expected_balance}, but got {account_deposit_response.balance}"
            )

        expected_fields = {
            "amount": account_deposit_request.balance,
            "type": "DEPOSIT",
            "relatedAccountId": account_deposit_request.id}
        assert account_deposit_response.transactions
        assert any(expected_fields.items() <= t.items() for t in account_deposit_response.transactions), (
            f"Expected to have created transaction {expected_fields} in account, but got {account_deposit_response.transactions}"
        )

        return account_deposit_response

    def deposit_money_to_invalid_account(self, user_request: CreateUserRequest, account_id: int):
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            id=account_id,
            balance=RandomData.get_deposit_balance(),
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
            id=account_id,
            balance=balance,
        )

        CrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.ACCOUNTS_DEPOSIT,
            ResponseSpecs.request_returns_bad_request_with_text(error_message)
        ).post(account_deposit_request)

    def deposit_money_with_empty_balance(self, user_request: CreateUserRequest, account_id: int, balance: str | None):
        account_deposit_request: AccountDepositRequest = AccountDepositRequest(
            id=account_id,
            balance=balance,
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

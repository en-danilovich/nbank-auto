from typing import List
import pytest
from playwright.sync_api import Page

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_account_response import CreateAccountResponse


@pytest.mark.ui
@pytest.mark.usefixtures("user_session_extension", "browser_match_guard")
class TestDepositMoney:
    @pytest.mark.skip(reason="UI breaking changes in deposit flow — disable until fixed")
    @pytest.mark.user_session(10)
    def test_deposit_money_to_account(self, page: Page, api_manager: ApiManager, user_request: CreateUserRequest):
        deposit_amount = RandomData.get_deposit_balance()
        user_dashboard = UserDashboard(page).open()
        account_number = user_dashboard.create_new_account()
        user_dashboard.click_deposit_money()\
            .select_account(account_number)\
            .enter_amount(deposit_amount)\
            .click_deposit()\
            .check_alert_message_and_accept(BankAlert.get_deposit_balance_success_msg(deposit_amount, account_number))\
            .get_page(UserDashboard)\
            .verify_page_is_visible()\
            .click_deposit_money()\
            .verify_account_balance_option(account_number, deposit_amount)

        user_accounts: List[CreateAccountResponse] = api_manager.user_steps.get_all_accounts(user_request)
        assert len(user_accounts) == 1
        assert user_accounts[0] and user_accounts[0].balance == deposit_amount

    @pytest.mark.user_session(10)
    def test_deposit_money_account_can_not_be_empty(self, page: Page, api_manager: ApiManager,
                                                    user_request: CreateUserRequest):
        user_dashboard = UserDashboard(page).open()
        user_dashboard.create_new_account()
        user_dashboard.click_deposit_money() \
            .enter_amount(RandomData.get_deposit_balance())\
            .click_deposit() \
            .check_alert_message_and_accept(BankAlert.SELECT_ACCOUNT)

        user_accounts: List[CreateAccountResponse] = api_manager.user_steps.get_all_accounts(user_request)
        assert len(user_accounts) == 1
        assert user_accounts[0] and user_accounts[0].balance == 0

    @pytest.mark.user_session(10)
    @pytest.mark.parametrize('amount, alert_msg', [
        (-0.01, BankAlert.ENTER_VALID_AMOUNT),
        (0, BankAlert.ENTER_VALID_AMOUNT),
        (5000.01, BankAlert.MAX_DEPOSIT_EXCEEDED),
    ])
    def test_deposit_money_not_valid_money_amount(self, page: Page, api_manager: ApiManager,
                                                  user_request: CreateUserRequest, amount: float, alert_msg: str):
        user_dashboard = UserDashboard(page).open()
        account_number = user_dashboard.create_new_account()
        user_dashboard.click_deposit_money() \
            .select_account(account_number)\
            .enter_amount(amount) \
            .click_deposit() \
            .check_alert_message_and_accept(alert_msg)

        user_accounts: List[CreateAccountResponse] = api_manager.user_steps.get_all_accounts(user_request)
        assert len(user_accounts) == 1
        assert user_accounts[0] and user_accounts[0].balance == 0

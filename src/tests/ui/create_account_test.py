from typing import List
import pytest
from playwright.sync_api import Page

from src.main.api.classes.api_manager import ApiManager
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_account_response import CreateAccountResponse


@pytest.mark.ui
@pytest.mark.usefixtures("user_session_extension", "browser_match_guard")
class TestCreateAccount:
    @pytest.mark.user_session(10)
    @pytest.mark.check_accounts_change(delta=1)
    def test_user_can_create_account(self, page: Page, api_manager: ApiManager, user_request: CreateUserRequest):
        UserDashboard(page).open() \
            .verify_page_is_visible()\
            .click_create_new_account()\
            .check_alert_message_and_accept(BankAlert.NEW_ACCOUNT_CREATED)\
            .verify_page_is_visible()

        accounts: List[CreateAccountResponse] = api_manager.user_steps.get_all_accounts(user_request)
        assert len(accounts) == 1
        assert accounts[0].balance == 0

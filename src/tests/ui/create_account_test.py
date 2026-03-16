from typing import List
import pytest
from playwright.sync_api import Page, expect

from src.main.api.classes.api_manager import ApiManager
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_account_response import CreateAccountResponse

@pytest.mark.ui
class TestCreateAccount:
    @pytest.mark.user_session(10)
    def test_user_can_create_account(self, page: Page, api_manager:ApiManager, user_request: CreateUserRequest):
        user_dashboard = UserDashboard(page).open()\
            .create_new_account()\
            .check_alert_message_and_accept(BankAlert.NEW_ACCOUNT_CREATED)
        expect(user_dashboard.welcome_text).to_be_visible()

        user_accounts: List[CreateAccountResponse] = api_manager.user_steps.get_all_accounts(user_request)
        assert len(user_accounts) == 1
        assert user_accounts[0] and user_accounts[0].balance == 0
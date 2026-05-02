import re

from playwright.sync_api import Dialog, expect

from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.ui.pages.base_page import BasePage
from src.main.ui.pages.deposit_page import DepositPage
from src.main.ui.pages.edit_profile_page import EditProfilePage
from src.main.ui.pages.transfer_page import TransferPage


class UserDashboard(BasePage):
    @property
    def dashboard_text(self):
        return self.page.get_by_text("User Dashboard")

    @property
    def create_new_account_button(self):
        return self.page.get_by_role("button", name="➕ Create New Account")

    @property
    def deposit_money_button(self):
        return self.page.get_by_role("button", name="💰 Deposit Money")

    @property
    def transfer_button(self):
        return self.page.get_by_role("button", name="🔄 Make a Transfer")

    @property
    def welcome_text(self):
        return self.page.locator("h2.welcome-text")

    @property
    def username_header(self):
        return self.page.locator(".profile-header")

    def url(self):
        return "/dashboard"

    def verify_page_is_visible(self):
        expect(self.dashboard_text).to_be_visible()
        return self

    def verify_welcome_text(self, name: str):
        expect(self.welcome_text.locator("span"),
               f"Welcome text span should contain '{name}'").to_have_text(name)
        return self

    def click_create_new_account(self):
        self.create_new_account_button.click()
        return self

    def click_username_in_header(self) -> EditProfilePage:
        self.username_header.click()
        return self.get_page(EditProfilePage)

    def click_make_transfer(self) -> TransferPage:
        with self.expect_api_response(Endpoint.GET_CUSTOMER_ACCOUNTS):
            self.transfer_button.click()
        return self.get_page(TransferPage)

    def click_deposit_money(self) -> DepositPage:
        with self.expect_api_response(Endpoint.GET_CUSTOMER_ACCOUNTS):
            self.deposit_money_button.click()
        return self.get_page(DepositPage)

    def create_new_account(self):
        message = ""

        def _handler(d: Dialog) -> None:
            nonlocal message
            message = d.message
            d.accept()
        self.page.once("dialog", _handler)

        with self.page.expect_event("dialog"):
            self.create_new_account_button.click()
            expect(self.dashboard_text).to_be_visible()

        return self._parse_account_number(message)

    def _parse_account_number(self, message: str):
        match = re.search(r"Account Number:\s*(\w+)", message)
        return match.group(1) if match else None

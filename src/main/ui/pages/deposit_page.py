from playwright.sync_api import expect

from src.main.ui.elements.account_select import AccountSelect
from src.main.ui.pages.base_page import BasePage


class DepositPage(BasePage):
    @property
    def account_select(self) -> AccountSelect:
        return AccountSelect(self.page.locator("select.account-selector"))

    @property
    def amount_input(self):
        return self.page.get_by_placeholder("Enter amount")

    @property
    def deposit_button(self):
        return self.page.get_by_role("button", name="💵 Deposit")

    def url(self):
        return "/deposit"

    def select_account(self, account_number: str):
        self.account_select.select_option_by_account_number(account_number)
        return self

    def enter_amount(self, amount: float):
        self.amount_input.fill(str(amount))
        return self

    def click_deposit(self):
        self.deposit_button.click()
        return self

    def verify_account_balance_option(self, account_number: str, balance: float):
        expect(self.account_select.get_option_by_account_number(account_number)).to_contain_text(f'${balance}')
        return self

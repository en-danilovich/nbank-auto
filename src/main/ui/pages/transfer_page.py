from src.main.ui.elements.account_select import AccountSelect
from src.main.ui.pages.base_page import BasePage


class TransferPage(BasePage):
    @property
    def account_select(self) -> AccountSelect:
        return AccountSelect(self.page.locator("select.account-selector"))

    @property
    def recipient_name_input(self):
        return self.page.get_by_placeholder("Enter recipient name")

    @property
    def recipient_account_input(self):
        return self.page.get_by_placeholder("Enter recipient account number")

    @property
    def amount_input(self):
        return self.page.get_by_placeholder("Enter amount")

    @property
    def confirm_checkbox(self):
        return self.page.get_by_role("checkbox", name="Confirm details are correct")

    @property
    def send_button(self):
        return self.page.get_by_role("button", name="🚀 Send Transfer")

    def url(self):
        return "/transfer"

    def select_account(self, account_number: str):
        self.account_select.select_option_by_account_number(account_number)
        return self

    def enter_recipient_name(self, name: str):
        self.recipient_name_input.fill(name)
        return self

    def enter_recipient_account(self, account_number: str):
        self.recipient_account_input.fill(account_number)
        return self

    def enter_amount(self, amount: float):
        self.amount_input.fill(str(amount))
        return self

    def check_confirm(self):
        self.confirm_checkbox.check()
        return self

    def click_send(self):
        with self.page.expect_event("dialog"):
            self.send_button.click()
        return self
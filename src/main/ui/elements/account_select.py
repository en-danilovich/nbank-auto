from playwright.sync_api import Locator

from src.main.ui.elements.base_element import BaseElement


class AccountSelect(BaseElement):
    def select_option_by_account_number(self, account_number: str):
        option = self.element.locator("option", has_text=account_number).first
        self.element.select_option(label=option.inner_text())
        return self

    def get_option_by_account_number(self, account_number: str) -> Locator:
        return self.element.locator("option", has_text=account_number).first

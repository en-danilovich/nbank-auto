from typing import List

from playwright.sync_api import expect, Locator

from src.main.ui.elements.user_badge import UserBadge
from src.main.ui.pages.base_page import BasePage


class AdminPanel(BasePage):
    @property
    def admin_panel_text(self):
        return self.page.get_by_text("Admin Panel")

    @property
    def add_user_button(self):
        return self.page.get_by_role("button", name="Add User")

    def url(self):
        return "/admin"

    def create_user(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.add_user_button.click()
        return self

    def get_all_users_locator(self) -> Locator:
        return self.page.locator(".card.shadow-custom:has(:has-text('All Users')) li")

    def get_all_users(self) -> List[UserBadge]:
        return self._generate_page_elements(self.get_all_users_locator(), UserBadge)

    def wait_for_username(self, username: str):
        expect(self.get_all_users_locator()).to_contain_text([username])
        return self

    def verify_page_is_visible(self):
        expect(self.admin_panel_text).to_be_visible()
        return self

    def check_user_visibility(self, username: str, is_visible: bool):
        match = any(u.username == username for u in self.get_all_users())
        if is_visible:
            assert match
        else:
            assert not match
        return self
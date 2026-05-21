from src.main.ui.pages.base_page import BasePage


class LoginPage(BasePage):
    @property
    def login_button(self):
        return self.page.get_by_role("button", name="Login")

    def url(self):
        return "/login"

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        return self

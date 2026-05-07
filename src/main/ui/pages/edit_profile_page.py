from playwright.sync_api import expect

from src.main.ui.pages.base_page import BasePage


class EditProfilePage(BasePage):
    @property
    def name_input(self):
        return self.page.get_by_placeholder("Enter new name")

    @property
    def save_button(self):
        return self.page.get_by_role("button", name="💾 Save Changes")

    @property
    def home_button(self):
        return self.page.get_by_role("button", name="🏠 Home")

    @property
    def edit_profile_header(self):
        return self.page.get_by_role("heading", name="✏️ Edit Profile")

    def url(self):
        return "/edit-profile"

    def verify_page_is_visible(self):
        expect(self.edit_profile_header).to_be_visible()
        self.page.wait_for_load_state('networkidle')
        return self

    def verify_name_is_loaded(self, expected_name: str):
        expect(self.name_input).to_have_value(expected_name)
        return self

    def enter_name(self, name: str):
        self.name_input.fill(name)
        expect(self.name_input).to_have_value(name)
        return self

    def click_save(self):
        with self.page.expect_event("dialog"):
            self.save_button.click()
        return self

    def click_home(self):
        from src.main.ui.pages.user_dashboard import UserDashboard
        self.home_button.click()
        return self.get_page(UserDashboard)

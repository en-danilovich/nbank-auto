from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar, Type

from playwright.sync_api import Page, Dialog, Locator, expect

from src.main.api.configs.config import Config
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.specs.request_specs import RequestSpecs

T = TypeVar("T", bound="BasePage")

class BasePage(ABC):
    def __init__(self, page: Page):
        self.page = page
        self.base_url = str(Config.get('UI_BASE_URL', "http://localhost:3000")).strip('/')

    def _generate_page_elements(self, element: Locator, constructor: Callable) -> list:
        count = element.count()
        if count == 0:
            return []
        element.first.wait_for(state="attached", timeout=10_000)
        return [constructor(element.nth(index)) for index in range(count)]

    def auth_as_user(self, user_request: CreateUserRequest) -> None:
        auth_token = RequestSpecs.auth_as_user(user_request.username, user_request.password).get("Authorization")
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.goto(self.base_url)
        self.page.evaluate('token => localStorage.setItem("authToken", token)', auth_token)

    @abstractmethod
    def url(self) -> str:
        raise NotImplementedError

    @property
    def username_input(self):
        return self.page.get_by_placeholder("Username")

    @property
    def password_input(self):
        return self.page.get_by_placeholder("Password")

    @property
    def header_user_name(self):
        return self.page.locator(".user-info span.user-name")

    def open(self: T) -> T:
        target = self.url()
        if self.base_url and target.startswith("/"):
            target = f'{self.base_url}{target}'
        self.page.goto(target, wait_until="domcontentloaded")
        return self

    def get_page(self, page_cls: Type[T]) -> T:
        return page_cls(self.page)

    def verify_header_username(self: T, expected_name: str) -> T:
        expect(self.header_user_name,
               f"Header name should be '{expected_name}'").to_have_text(expected_name)
        return self

    def expect_api_response(self, endpoint: Endpoint, status: int = 200):
        api_url = f"{self.base_url}{Config.get('api_version')}{endpoint.value.url}"
        return self.page.expect_response(lambda res: res.url == api_url and res.status == status)

    def check_alert_message_and_accept(self: T, expected_text: str | list[str]) -> T:
        def _handler(d: Dialog) -> None:
            candidates = [expected_text] if isinstance(expected_text, str) else expected_text
            assert any(c in d.message for c in candidates), f"Alert text mismatch: {d.message}"
            d.accept()
        self.page.once("dialog", _handler)
        return self

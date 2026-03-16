from playwright.sync_api import Locator


class BaseElement:
    def __init__(self, element: Locator):
        self.element: Locator = element

    def find(self, selector: str) -> Locator:
        return self.element.locator(selector)

    def find_all(self, selector: str) -> Locator:
        return self.element.locator(selector)
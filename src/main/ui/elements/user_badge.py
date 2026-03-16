from src.main.ui.elements.base_element import BaseElement


class UserBadge(BaseElement):
    @property
    def _lines(self):
        text = self.element.inner_text()
        return text.splitlines()

    @property
    def username(self) -> str:
        return self._lines[0] if self._lines else ""

    @property
    def role(self) -> str:
        return self._lines[1] if len(self._lines) > 1 else ""
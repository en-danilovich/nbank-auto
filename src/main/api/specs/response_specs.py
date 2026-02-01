from http import HTTPStatus
from typing import Callable
from requests import Response


class ResponseSpecs:
    @staticmethod
    def _make_status_checker(expected_statuses: list[HTTPStatus]) -> Callable[[Response], None]:
        def check(response: Response):
            assert response.status_code in expected_statuses, (
                f"Expected status {expected_statuses}, but got {response.status_code}. "
                f"Response body: {response.text}"
            )
        return check

    @staticmethod
    def request_returns_ok() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.OK])

    @staticmethod
    def entity_was_created() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.CREATED])

    @staticmethod
    def entity_was_deleted() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.OK, HTTPStatus.NO_CONTENT])

    @staticmethod
    def request_returns_bad_request_multiple_errors(
        error_key: str,
        error_value: str
    ) -> Callable[[Response], None]:
        def check(response: Response):
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f"Expected 400 BAD_REQUEST, got {response.status_code}. Response: {response.text}"
            )
            actual_value = response.json().get(error_key)
            assert error_value in actual_value, (
                f"Expected error field '{error_key}' to be '{error_value}', but got '{actual_value}'."
            )
        return check

    @staticmethod
    def request_returns_bad_request_with_text(
            error_message: str
    ) -> Callable[[Response], None]:
        def check(response: Response):
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f"Expected 400 BAD_REQUEST, got {response.status_code}. Response: {response.text}"
            )
            actual_value = response.text
            assert error_message == actual_value, (
                f"Expected error message '{error_message}', but got '{actual_value}'."
            )

        return check

    @staticmethod
    def unauthorized_request() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.UNAUTHORIZED])

    @staticmethod
    def action_forbidden() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.FORBIDDEN])

    @staticmethod
    def internal_server_error() -> Callable[[Response], None]:
        return ResponseSpecs._make_status_checker([HTTPStatus.INTERNAL_SERVER_ERROR])
import requests
import logging

from src.main.api.models.login_user_request import LoginUserRequest
from typing import Dict

from src.main.api.configs.config import Config
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.specs.response_specs import ResponseSpecs


class RequestSpecs:
    @staticmethod
    def _base_url() -> str:
        return f"{Config.get('server')}{Config.get('apiVersion')}"

    @staticmethod
    def default_req_headers() -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @staticmethod
    def unauth_spec() -> Dict[str, str]:
        return RequestSpecs.default_req_headers()

    @staticmethod
    def admin_auth_spec():
        headers = RequestSpecs.default_req_headers()
        headers["Authorization"] = Config.get("ADMIN_AUTH_HEADER", "Basic YWRtaW46YWRtaW4=")
        return headers

    @staticmethod
    def auth_as_user(username, password):
        try:
            response: requests.Response = CrudRequester(
                RequestSpecs.unauth_spec(),
                Endpoint.LOGIN_USER,
                ResponseSpecs.request_returns_ok()
            ).post(LoginUserRequest(username=username, password=password))
        except:
            logging.error(f"Authentication failed for {username}")
            raise Exception("Failed to authenticate user")
        else:
            auth_header = response.headers.get("Authorization")
            headers = RequestSpecs.default_req_headers()
            headers["Authorization"] = auth_header
            return headers
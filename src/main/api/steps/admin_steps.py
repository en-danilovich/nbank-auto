from typing import List
from src.main.api.models.comparison.model_assertions import ModelAssertions
from src.main.api.requests.skeleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.main.api.models.create_user_response import CreateUserResponse
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.steps.base_steps import BaseSteps
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs


class AdminSteps(BaseSteps):
    def create_user(self, user_request: CreateUserRequest):
        create_user_response: CreateUserResponse = ValidatedCrudRequester(
            RequestSpecs.admin_auth_spec(),
            Endpoint.ADMIN_CREATE_USER,
            ResponseSpecs.entity_was_created()
        ).post(user_request)
        ModelAssertions(user_request, create_user_response).match()

        self.created_objects.append(create_user_response)

        return create_user_response
    
    def create_invalid_user(self, user_request: CreateUserRequest, error_key: str, error_value: str):
        CrudRequester(
            RequestSpecs.admin_auth_spec(),
            Endpoint.ADMIN_CREATE_USER,
            ResponseSpecs.request_returns_bad_request_multiple_errors(error_key, error_value)
        ).post(user_request)

    def delete_user(self, user_id: int):
        CrudRequester(
            RequestSpecs.admin_auth_spec(),
            Endpoint.ADMIN_DELETE_USER,
            ResponseSpecs.entity_was_deleted()
        ).delete(user_id)

    def get_all_users(self) -> List[CreateUserRequest]:
        response = ValidatedCrudRequester(
            RequestSpecs.admin_auth_spec(),
            Endpoint.ADMIN_GET_ALL_USERS,
            ResponseSpecs.request_returns_ok()
        ).get()
        return response

    def get_all_users_as(self, admin_user_request: CreateUserRequest) -> List[CreateUserRequest]:
        response = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(admin_user_request.username, admin_user_request.password),
            Endpoint.ADMIN_GET_ALL_USERS,
            ResponseSpecs.request_returns_ok()
        ).get()
        return response
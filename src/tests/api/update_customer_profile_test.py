import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


class TestUpdateCustomerProfile(BaseTest):
    def test_update_customer_profile_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.UPDATE_CUSTOMER_PROFILE,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.usefixtures('api_manager', 'user_request')
    @pytest.mark.parametrize('update_customer_profile_request',
                             [RandomModelGenerator.generate(UpdateCustomerProfileRequest),
                              UpdateCustomerProfileRequest(name='A a')])
    def test_update_customer_profile(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                     update_customer_profile_request: UpdateCustomerProfileRequest):
        api_manager.user_steps.update_profile(user_request, update_customer_profile_request)
        assert api_manager.user_steps.get_profile(user_request).name == update_customer_profile_request.name, (
            "Verify user.name was not changed"
        )

    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.usefixtures('api_manager', 'user_request')
    @pytest.mark.parametrize('name',
                             [
                                 RandomData.get_word(),
                                 '',
                                 '   ',
                                 '0123456789',
                                 f'{RandomData.get_int(0, 9)}Adfadsf dafs',
                                 f'Adfadsf dafs{RandomData.get_int(0, 9)}',
                                 f'dsfaf{RandomData.get_special_symbol} bczxv',
                                 f'dsfaf bc{RandomData.get_special_symbol}zxv',
                                 f'{RandomData.get_word()}_{RandomData.get_word()}',
                                 f'{RandomData.get_word()}.{RandomData.get_word()}',
                                 f'{RandomData.get_word()}  {RandomData.get_word()}',
                             ])
    def test_update_customer_profile_incorrect_name(self, api_manager: ApiManager, user_request: CreateUserRequest,
                                                    name: str):
        profile_name = api_manager.user_steps.get_profile(user_request).name
        api_manager.user_steps.update_profile_using_invalid_data(user_request,
                                                                 UpdateCustomerProfileRequest(name=name),
                                                                 'Name must contain two words with letters only')
        assert api_manager.user_steps.get_profile(user_request).name == profile_name, (
            "Verify user.name was not changed"
        )

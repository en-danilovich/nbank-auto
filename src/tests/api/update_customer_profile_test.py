import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.tests.api.base_api_test import BaseTest


@pytest.mark.api_version("with_database")
class TestUpdateCustomerProfile(BaseTest):
    def test_update_customer_profile_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.UPDATE_CUSTOMER_PROFILE,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.check_profile_name(expected_source="update_customer_profile_request.name")
    @pytest.mark.parametrize('update_customer_profile_request',
                             [RandomModelGenerator.generate(UpdateCustomerProfileRequest),
                              UpdateCustomerProfileRequest(name='A a')])
    def test_update_customer_profile(self, api_manager: ApiManager, prepared_users,
                                     update_customer_profile_request: UpdateCustomerProfileRequest):
        user = prepared_users[0]
        update_response = api_manager.user_steps.update_profile(user, update_customer_profile_request)

        user_dao = api_manager.database_steps.get_user_by_username(user.username)
        DaoAndModelAssertions.assert_that(update_response.customer, user_dao).match()

    @pytest.mark.prepare_users(number=1)
    @pytest.mark.check_profile_name()
    @pytest.mark.parametrize('name',
                             [
                                 RandomData.get_word(),
                                 '',
                                 '   ',
                                 '0123456789',
                                 f'{RandomData.get_int(0, 9)}Adfadsf dafs',
                                 f'Adfadsf dafs{RandomData.get_int(0, 9)}',
                                 f'dsfaf{RandomData.get_special_symbol()} bczxv',
                                 f'dsfaf bc{RandomData.get_special_symbol()}zxv',
                                 f'{RandomData.get_word()}_{RandomData.get_word()}',
                                 f'{RandomData.get_word()}.{RandomData.get_word()}',
                                 f'{RandomData.get_word()}  {RandomData.get_word()}',
                             ])
    def test_update_customer_profile_incorrect_name(self, api_manager: ApiManager, prepared_users,
                                                    name: str):
        user = prepared_users[0]
        api_manager.user_steps.update_profile_using_invalid_data(user,
                                                                 UpdateCustomerProfileRequest(name=name),
                                                                 'Name must contain two words with letters only')

        user_dao = api_manager.database_steps.get_user_by_username(user.username)
        assert user_dao.name is None, f"Name should remain unchanged in DB after invalid update, but got: {user_dao.name!r}"

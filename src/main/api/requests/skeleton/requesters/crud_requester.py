from typing import Optional, TypeVar
import requests


from src.main.api.configs.config import Config
from src.main.api.models.base_model import BaseModel
from src.main.api.requests.skeleton.http_request import HttpRequest
from src.main.api.requests.skeleton.interfaces.crud_end_interface import CrudEndpointInterface


T = TypeVar('T', bound=BaseModel)


class CrudRequester(HttpRequest, CrudEndpointInterface):
    @property
    def base_url(self) -> str:
        return f"{Config.get('server')}{Config.get('server_api_version')}"
    
    def post(self, model: Optional[T] = None) -> requests.Response:
        body = model.model_dump() if model is not None else ''

        response = requests.post(
            url=f'{self.base_url}{self.endpoint.value.url}',
            headers=self.request_spec,
            json=body
        )
        self.response_spec(response)
        return response

    def get(self, id: Optional[int] = None): 
        response = requests.get(
            url=f'{self.base_url}{self.endpoint.value.url}{("/" + str(id)) if id is not None else ""}',
            headers=self.request_spec
        )
        self.response_spec(response)
        return response

    def update(self, model: Optional[BaseModel] = None, id: Optional[int] = None) -> requests.Response:
        body = model.model_dump() if model is not None else ''

        url = f'{self.base_url}{self.endpoint.value.url}{("/" + str(id)) if id is not None else ""}'
        response = requests.put(
            url=url,
            headers=self.request_spec,
            json=body
        )
        self.response_spec(response)
        return response

    def delete(self, id: int) -> requests.Response:
        response = requests.delete(
            url=f'{self.base_url}{self.endpoint.value.url}/{id}',
            headers=self.request_spec
        )
        self.response_spec(response)
        return response
from typing import Optional, TypeVar
import requests


from src.main.api.configs.config import Config
from src.main.api.models.base_model import BaseModel
from src.main.api.requests.skeleton.http_request import HttpRequest
from src.main.api.requests.skeleton.interfaces.crud_end_interface import CrudEndpointInterface
from src.main.api.utils.coverage import coverage_path_for, get_tracker


T = TypeVar('T', bound=BaseModel)


class CrudRequester(HttpRequest, CrudEndpointInterface):
    @property
    def base_url(self) -> str:
        return f"{Config.get('SERVER')}{Config.get('SERVER_API_VERSION')}"

    def _tracked(self, id_in_path: bool, func):
        path = coverage_path_for(self.endpoint, id_in_path=id_in_path)
        return get_tracker().track_coverage_requests(path)(func)

    def post(self, model: Optional[T] = None) -> requests.Response:
        body = model.model_dump() if model is not None else ''
        url = f'{self.base_url}{self.endpoint.value.url}'

        def _call() -> requests.Response:
            return requests.post(url=url, headers=self.request_spec, json=body)

        response = self._tracked(id_in_path=False, func=_call)()
        self.response_spec(response)
        return response

    def get(self, id: Optional[int] = None):
        suffix = f"/{id}" if id is not None else ""
        url = f'{self.base_url}{self.endpoint.value.url}{suffix}'

        def _call() -> requests.Response:
            return requests.get(url=url, headers=self.request_spec)

        response = self._tracked(id_in_path=id is not None, func=_call)()
        self.response_spec(response)
        return response

    def update(self, model: Optional[BaseModel] = None, id: Optional[int] = None) -> requests.Response:
        body = model.model_dump() if model is not None else ''
        suffix = f"/{id}" if id is not None else ""
        url = f'{self.base_url}{self.endpoint.value.url}{suffix}'

        def _call() -> requests.Response:
            return requests.put(url=url, headers=self.request_spec, json=body)

        response = self._tracked(id_in_path=id is not None, func=_call)()
        self.response_spec(response)
        return response

    def delete(self, id: int) -> requests.Response:
        url = f'{self.base_url}{self.endpoint.value.url}/{id}'

        def _call() -> requests.Response:
            return requests.delete(url=url, headers=self.request_spec)

        response = self._tracked(id_in_path=True, func=_call)()
        self.response_spec(response)
        return response

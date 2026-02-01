from typing import Optional, TypeVar
from pydantic import TypeAdapter

from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.models.base_model import BaseModel
from src.main.api.requests.skeleton.http_request import HttpRequest


T = TypeVar('T', bound=BaseModel)


class ValidatedCrudRequester(HttpRequest):
    def __init__(self, request_spec, endpoint, response_spec):
        super().__init__(request_spec, endpoint, response_spec)
        self.crud_requester = CrudRequester(
            request_spec=request_spec,
            endpoint=endpoint,
            response_spec=response_spec
        )
        self._adapter = TypeAdapter(self.endpoint.value.response_model)

    def post(self, model: Optional[T] = None):
        response = self.crud_requester.post(model)
        return self._adapter.validate_python(response.json())
    
    def get(self, id: Optional[int] = None): 
        response = self.crud_requester.get(id)
        return self._adapter.validate_python(response.json())

    def update(self, id: int): ...
    def delete(self, id: int): ...

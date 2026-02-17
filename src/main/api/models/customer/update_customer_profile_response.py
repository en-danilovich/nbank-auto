from typing import Any, Dict, List

from src.main.api.models.base_model import BaseModel

class UpdateCustomerInfo(BaseModel):
    id: int
    username: str
    password: str
    name: str
    role: str
    accounts: List[Dict[str, Any]]

class UpdateCustomerProfileResponse(BaseModel):
    message: str
    customer: UpdateCustomerInfo



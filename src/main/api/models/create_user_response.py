from typing import Optional, List, Dict, Any

from src.main.api.models.base_model import BaseModel


class CreateUserResponse(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    role: str
    accounts: List[Dict[str, Any]] = []
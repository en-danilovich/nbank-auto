from src.main.api.models.base_model import BaseModel


class UpdateCustomerProfileResponse(BaseModel):
    id: int
    username: str
    name: str | None
    role: str

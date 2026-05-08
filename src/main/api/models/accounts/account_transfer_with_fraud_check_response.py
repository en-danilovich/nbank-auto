from src.main.api.models.base_model import BaseModel


class AccountTransferWithFraudCheckResponse(BaseModel):
    status: str
    message: str
    amount: float
    senderAccountId: int
    receiverAccountId: int
    fraudRiskScore: float
    fraudReason: str
    requiresManualReview: bool
    requiresVerification: bool

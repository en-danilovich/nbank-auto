from enum import Enum


class BankAlert(str, Enum):
    USER_CREATED_SUCCESSFULLY = "✅ User created successfully!"
    USERNAME_MUST_BE_BETWEEN_3_AND_15_CHARACTERS = "username: size must be between 3 and 15"
    NEW_ACCOUNT_CREATED = "✅ New Account Created! Account Number:"
    SELECT_ACCOUNT = "❌ Please select an account."
    ENTER_VALID_AMOUNT = "❌ Please enter a valid amount."
    MAX_DEPOSIT_EXCEEDED = "❌ Please deposit less or equal to 5000$."
    PROFILE_UPDATED_SUCCESSFULLY = "✅ Name updated successfully!"
    ENTER_VALID_NAME = "❌ Please enter a valid name."
    NAME_IS_SAME_AS_CURRENT = "⚠️ New name is the same as the current one."
    NAME_MUST_CONTAIN_TWO_WORDS = "Name must contain two words with letters only"
    # Frontend currently passes the raw error response object to alert() instead of
    # extracting `.message`, so JS stringifies it as "[object Object]".
    INVALID_NAME_RAW_OBJECT = "[object Object]"
    FILL_ALL_FIELDS = "❌ Please fill all fields and confirm."
    RECIPIENT_NAME_MISMATCH = "❌ The recipient name does not match the registered name."
    TRANSFER_MIN_AMOUNT = "❌ Error: Transfer amount must be at least 0.01"
    TRANSFER_MAX_AMOUNT = "❌ Error: Transfer amount cannot exceed 10000"
    TRANSFER_INSUFFICIENT_FUNDS = "❌ Error: Invalid transfer: insufficient funds or invalid accounts"
    TRANSFER_TO_SAME_ACCOUNT = "❌ You cannot transfer money to the same account."

    @staticmethod
    def get_deposit_balance_success_msg(amount: float, account_number: str) -> str:
        return f"✅ Successfully deposited ${amount} to account {account_number}!"

    @staticmethod
    def get_transfer_success_msg(amount: float, account_number: str) -> str:
        return f"✅ Successfully transferred ${amount} to account {account_number}!"

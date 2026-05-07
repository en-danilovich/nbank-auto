from src.main.api.database.dao.account_dao import AccountDao
from src.main.api.database.dao.user_dao import UserDao
from src.main.api.database.db_client import DBRequest, RequestType, Condition


class DataBaseSteps:
    @staticmethod
    def get_user_by_username(username: str) -> UserDao:
        return DBRequest.builder() \
            .request_type(RequestType.SELECT) \
            .table("customers") \
            .where(Condition.equal_to("username", username)) \
            .extract_as(UserDao)

    @staticmethod
    def find_user_by_username(username: str):
        """
        Optional variant of get_user_by_username().
        Returns None when user doesn't exist (useful for negative assertions).
        """
        return DBRequest.builder() \
            .request_type(RequestType.SELECT) \
            .table("customers") \
            .where(Condition.equal_to("username", username)) \
            .extract_optional_as(UserDao)

    @staticmethod
    def get_account_by_account_number(account_number: str) -> AccountDao:
        return DBRequest.builder() \
            .request_type(RequestType.SELECT) \
            .table("accounts") \
            .where(Condition.equal_to("account_number", account_number)) \
            .extract_as(AccountDao)

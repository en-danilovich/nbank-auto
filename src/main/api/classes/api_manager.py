from src.main.api.steps.admin_steps import AdminSteps
from src.main.api.steps.database_steps import DataBaseSteps
from src.main.api.steps.user_steps import UserSteps


class ApiManager:
    def __init__(self, created_objects: list):
        self.admin_steps = AdminSteps(created_objects)
        self.user_steps = UserSteps(created_objects)
        self.database_steps = DataBaseSteps

from typing import Any, List


class BaseSteps:
    def __init__(self, created_objects: List[Any]):
        self.created_objects = created_objects

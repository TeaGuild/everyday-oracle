from typing import List
from metaforecasting.models import ForecastType


class ForecasterQuestionTypeNotSupported(NotImplementedError):
    pass


class BaseForecaster:
    name: str
    authority: int

    supported_questions: List[ForecastType]

    def get_prediction(self, q_id):
        raise NotImplementedError

    def search(self, s):
        raise NotImplementedError

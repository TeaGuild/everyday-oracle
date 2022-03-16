from typing import List
from models import ForecastType


class ForecasterQuestionTypeNotSupported(NotImplementedError):
    pass


class BaseForecaster:
    name: str
    authority: int

    supported_questions: List[ForecastType]

    def get_prediction(self, q_id, *args, **kwargs):
        raise NotImplementedError

    def search(self, s, *args, **kwargs):
        raise NotImplementedError

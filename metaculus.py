from typing import List, Optional
from forecasters import BaseForecaster, ForecasterQuestionTypeNotSupported
from models import (
    ForecastMetaculusData,
    ForecastType,
    MetaculusCommunityFullPrediction,
    MetaculusCommunityPrediction,
)
import httpx
from dateutil import parser as dt_parser

METACULUS_URL = "https://www.metaculus.com"
TIME_FORMAT = "%d.%m.%Y %H:%M"


class MetaculusIDNotFound(BaseException):
    pass


class MetaculusForecaster(BaseForecaster):
    def _get_raw_metaculus(self, q_id: int):
        a = httpx.get(f"{METACULUS_URL}/api2/questions/{q_id}", follow_redirects=True)
        if a.status_code == 404:
            raise MetaculusIDNotFound

        return a.json()

    def get_prediction(self, q_id: int) -> ForecastMetaculusData:
        return self.format_prediction(self._get_raw_metaculus(q_id))

    def format_prediction(self, raw: dict) -> Optional[ForecastMetaculusData]:
        metaculus_pos = raw["possibilities"]

        if metaculus_pos["type"] == "binary":
            forecast_type = ForecastType.binary

        else:
            # we should implement other types sooner
            return None

        m_c_p = raw["community_prediction"]

        try:
            prediction = MetaculusCommunityPrediction(
                full=MetaculusCommunityFullPrediction(
                    y=m_c_p["full"]["y"],
                    q1=int(m_c_p["full"]["q1"] * 100),
                    q2=int(m_c_p["full"]["q2"] * 100),
                    q3=int(m_c_p["full"]["q3"] * 100),
                )
            )
        except KeyError:
            print(f"No keys on {raw['id']}")
            prediction = None  # TODO: fix crutch

        data = ForecastMetaculusData(
            platform="metaculus",
            id_on_platform=raw["id"],
            forecast_type=forecast_type,
            question_title=raw["title"],
            question_url=f'{METACULUS_URL}{raw["page_url"]}',
            created_time=dt_parser.parse(raw["created_time"]),
            votes=raw["votes"],
            activity=raw["activity"],
            community_prediction=prediction,
            total_predictions=raw["number_of_predictions"],
            close_time=dt_parser.parse(raw["close_time"]),
            resolve_time=dt_parser.parse(raw["resolve_time"]),
        )

        return data

    def format_as_html(self, data: ForecastMetaculusData) -> str:
        return (
            f"<b>{data.question_title}</b> (ID: {data.id_on_platform})\n"
            f'<a href="{data.question_url}">Ссылка</a>\n\n'
            f"🔮 Текущие вероятности (q1, q2, q3): <b>"
            f"{data.community_prediction.full.q1}%, {data.community_prediction.full.q2}%, "
            f"{data.community_prediction.full.q3}% </b>\n\n"
            f"⏱ Время закрытия вопроса: <b>{data.close_time.strftime(TIME_FORMAT)}</b>\n"
            f"🔔 Время завершения события: <b>{data.resolve_time.strftime(TIME_FORMAT)}</b>\n"
            f"👤 Всего предсказаний сообщества: <b>{data.total_predictions}</b>"
        )

    def search(
        self, s: str, display_popular: bool = True, limit: int = 10, offset: int = 0
    ) -> List[ForecastMetaculusData]:
        params = {"order_by": "-activity", "limit": limit, "offset": offset}
        if s == "" and not display_popular:
            return []
        if s != "":
            params["search"] = s
        a = httpx.get(f"{METACULUS_URL}/api2/questions/", params=params)
        return list([self.format_prediction(i) for i in a.json()["results"]])

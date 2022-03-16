from typing import List, Optional
from metaforecasting.forecasters import BaseForecaster
from metaforecasting.models import (
    ForecastMetaculusData,
    ForecastType,
    MetaculusCommunityFullPrediction,
    MetaculusCommunityPrediction,
)
import httpx
from dateutil import parser as dt_parser
from loguru import logger


class MetaculusIDNotFound(BaseException):
    pass


class MetaculusForecaster(BaseForecaster):
    def __init__(self, metaculus_url="https://www.metaculus.com"):
        logger.info(f"Initiated `MetaculusForecaster` with URL: {metaculus_url}")
        self.url = metaculus_url

    def _get_raw_metaculus(self, q_id: int):
        a = httpx.get(f"{self.url}/api2/questions/{q_id}", follow_redirects=True)
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
            logger.debug(f"Ignoring this data, cuz it's {metaculus_pos['type']}")
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
            logger.debug(f"No keys on {raw['id']}")
            prediction = None  # TODO: fix crutch

        data = ForecastMetaculusData(
            platform="metaculus",
            id_on_platform=raw["id"],
            forecast_type=forecast_type,
            question_title=raw["title"],
            question_url=f'{self.url}{raw["page_url"]}',
            created_time=dt_parser.parse(raw["created_time"]),
            votes=raw["votes"],
            activity=raw["activity"],
            community_prediction=prediction,
            total_predictions=raw["number_of_predictions"],
            close_time=dt_parser.parse(raw["close_time"]),
            resolve_time=dt_parser.parse(raw["resolve_time"]),
        )

        return data

    def search(
        self, s: str, display_popular: bool = True, limit: int = 10, offset: int = 0
    ) -> List[ForecastMetaculusData]:
        params = {"order_by": "-activity", "limit": limit, "offset": offset}
        if s == "" and not display_popular:
            return []
        if s != "":
            params["search"] = s
        a = httpx.get(f"{self.url}/api2/questions/", params=params)
        return list([self.format_prediction(i) for i in a.json()["results"]])

"""
Current Air Quality Service
Aggregates verified environmental parameters and computes CPCB AQI.
Provenance is strictly labeled as 'model_estimate' (never CPCB observed or ground truth).
"""
from typing import Optional
from backend.app.schemas.current import AirQualityReading, CpcbBand
from backend.app.repositories.air_quality_repository import AirQualityRepository
from backend.app.repositories.weather_repository import WeatherRepository
from backend.app.repositories.traffic_repository import TrafficRepository
from backend.app.utils.cpcb_aqi import estimate_aqi_from_pm25, get_band_from_aqi


class CurrentAirQualityService:
    """Service providing current verified air quality metrics for Pune."""

    def __init__(
        self,
        aq_repo: Optional[AirQualityRepository] = None,
        weather_repo: Optional[WeatherRepository] = None,
        traffic_repo: Optional[TrafficRepository] = None,
    ):
        self._aq_repo = aq_repo or AirQualityRepository()
        self._weather_repo = weather_repo or WeatherRepository()
        self._traffic_repo = traffic_repo or TrafficRepository()

    def get_current_reading(self) -> AirQualityReading:
        """
        Retrieves the current verified air quality reading for Pune.
        Computes India CPCB AQI and band from PM2.5 concentration.
        """
        aq_data = self._aq_repo.get_latest_pm25_reading()
        weather_data = self._weather_repo.get_latest_weather()
        traffic_data = self._traffic_repo.get_latest_traffic()

        pm25 = float(aq_data["pm25"])
        aqi = estimate_aqi_from_pm25(pm25)
        aqi_band_str = get_band_from_aqi(aqi)

        return AirQualityReading(
            timestamp=aq_data["timestamp"],
            city="Pune",
            station=aq_data["station"],
            pm25=pm25,
            pm10=float(aq_data.get("pm10", 0.0)),
            aqi=aqi,
            aqiBand=CpcbBand(aqi_band_str),
            temperatureC=float(weather_data["temperatureC"]),
            humidityPct=float(weather_data["humidityPct"]),
            trafficIndex=float(traffic_data["trafficIndex"]),
            windSpeedKmh=float(weather_data["windSpeedKmh"]),
            dataSource="model_estimate",
        )

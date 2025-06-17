import logging
import httpx
from typing import TypedDict, Annotated, cast
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
from cachetools import TTLCache

app = FastAPI(
    title="Weather and Solar Energy Forecast API",
    description="API for fetching 7-day weather forecast and estimating solar energy production.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"
SOLAR_INSTALLATION_POWER_KW = 2.5
PANEL_EFFICIENCY = 0.2

class DailyForecast(BaseModel):
    date: date
    weather_code: int
    temperature_min_celsius: float
    temperature_max_celsius: float
    estimated_energy_kwh: float

class WeeklySummary(BaseModel):
    average_weekly_pressure_hPa: float
    average_weekly_sunshine_hours: float
    weekly_min_temperature_celsius: float
    weekly_max_temperature_celsius: float
    weekly_weather_summary: str

class DailyWeatherData(TypedDict):
    time: list[str]
    weather_code: list[int | None]
    temperature_2m_max: list[float | None]
    temperature_2m_min: list[float | None]
    sunshine_duration: list[float | None]
    precipitation_sum: list[float | None]

class HourlyWeatherData(TypedDict):
    time: list[str]
    pressure_msl: list[float | None]

class OpenMeteoResponse(TypedDict):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    daily_units: dict[str, str]
    daily: DailyWeatherData
    hourly_units: dict[str, str]
    hourly: HourlyWeatherData

cache: TTLCache[str, OpenMeteoResponse] = TTLCache(maxsize=100, ttl=60)

async def _fetch_open_meteo_data(
    latitude: float,
    longitude: float,
    cache_prefix: str,
    daily_params: list[str] | None = None,
    hourly_params: list[str] | None = None,
) -> OpenMeteoResponse:
    """
    Internal helper function to fetch data from Open-Meteo API with caching and error handling.
    """
    cache_key = f"{cache_prefix}_{latitude}_{longitude}"
    if cache_key in cache:
        return cache[cache_key]

    params: dict[str, float | int | str | list[str]] = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "forecast_days": 7,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    if daily_params:
        params["daily"] = daily_params
    if hourly_params:
        params["hourly"] = hourly_params

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPEN_METEO_API_URL, params=params, timeout=10.0)
            _ = response.raise_for_status()
            data = cast(OpenMeteoResponse, response.json())
            cache[cache_key] = data
            return data
    except httpx.RequestError as exc:
        logger.error(f"Error connecting to Open-Meteo API for {cache_prefix}: {exc}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Open-Meteo API, probably rate-limited.")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response from Open-Meteo API for {cache_prefix}: {exc.response.text}")
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Error response from Open-Meteo API: {exc.response.text}"
        )
    except Exception as exc:
        logger.error(f"An unexpected error occurred for {cache_prefix}: {exc}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {exc}")


async def fetch_forecast_data(latitude: float, longitude: float) -> OpenMeteoResponse:
    """
    Helper function to get daily forecast data from Open-Meteo API with caching.
    """
    daily_fields = ["weather_code", "temperature_2m_max", "temperature_2m_min", "sunshine_duration"]
    return await _fetch_open_meteo_data(
        latitude=latitude,
        longitude=longitude,
        cache_prefix="forecast",
        daily_params=daily_fields
    )


async def fetch_summary_data(latitude: float, longitude: float) -> OpenMeteoResponse:
    """
    Helper function to get daily and hourly data for the weekly summary from Open-Meteo API with caching.
    """
    daily_fields = ["temperature_2m_max", "temperature_2m_min", "sunshine_duration", "precipitation_sum"]
    hourly_fields = ["pressure_msl"]
    return await _fetch_open_meteo_data(
        latitude=latitude,
        longitude=longitude,
        cache_prefix="summary",
        daily_params=daily_fields,
        hourly_params=hourly_fields
    )

@app.get("/forecast", response_model=list[DailyForecast])
async def get_daily_forecast(
    latitude: Annotated[float, Query(..., gt=-90, le=90, description="Geographical latitude")],
    longitude: Annotated[float, Query(..., gt=-180, le=180, description="Geographical longitude")],
) -> list[DailyForecast]:
    """
    Retrieves a 7-day weather forecast and estimates solar energy production for a given location.
    """
    weather_data = await fetch_forecast_data(latitude, longitude)

    forecast_list: list[DailyForecast] = []
    
    daily_info = weather_data.get("daily")
    
    if not daily_info or "time" not in daily_info:
        raise HTTPException(status_code=500, detail="No daily forecast data available from API.")

    dates = daily_info.get("time", [])
    weather_codes = daily_info.get("weather_code", [])
    temp_maxes = daily_info.get("temperature_2m_max", [])
    temp_mins = daily_info.get("temperature_2m_min", [])
    sunshine_durations = daily_info.get("sunshine_duration", [])  # in seconds

    for i in range(len(dates)):
        if any(v is None for v in [dates[i], weather_codes[i], temp_mins[i], temp_maxes[i], sunshine_durations[i]]):
            continue
            
        exposure_time_hours = (sunshine_durations[i] or 0) / 3600
        
        estimated_energy_kwh = SOLAR_INSTALLATION_POWER_KW * exposure_time_hours * PANEL_EFFICIENCY

        forecast_list.append(
            DailyForecast(
                date=date.fromisoformat(dates[i]),
                weather_code=weather_codes[i], # pyright: ignore[reportArgumentType]
                temperature_min_celsius=temp_mins[i], # pyright: ignore[reportArgumentType]
                temperature_max_celsius=temp_maxes[i], # pyright: ignore[reportArgumentType]
                estimated_energy_kwh=round(estimated_energy_kwh, 2),
            )
        )
    return forecast_list

@app.get("/summary", response_model=WeeklySummary)
async def get_weekly_summary(
    latitude: Annotated[float, Query(..., gt=-90, le=90, description="Geographical latitude")],
    longitude: Annotated[float, Query(..., gt=-180, le=180, description="Geographical longitude")],
) -> WeeklySummary:
    """
    Provides a summary of weather conditions for the upcoming 7 days, including average pressure,
    average sunshine, extreme temperatures, and a general weather comment.
    """
    weather_data = await fetch_summary_data(latitude, longitude)

    daily_info = weather_data.get("daily")
    hourly_info = weather_data.get("hourly")

    if not daily_info or "time" not in daily_info:
        raise HTTPException(status_code=500, detail="No daily forecast data available from API.")
    if not hourly_info or "pressure_msl" not in hourly_info:
        raise HTTPException(status_code=500, detail="No hourly pressure data available from API.")

    temp_maxes: list[float | None] = daily_info.get("temperature_2m_max", [])
    temp_mins: list[float | None] = daily_info.get("temperature_2m_min", [])
    sunshine_durations: list[float | None] = daily_info.get("sunshine_duration", [])
    precipitation_sums: list[float | None] = daily_info.get("precipitation_sum", [])
    hourly_pressures: list[float | None] = hourly_info.get("pressure_msl", [])
    hourly_times: list[str] = hourly_info.get("time", [])

    daily_pressures: list[float] = []
    current_day: date | None = None
    current_day_pressures: list[float] = []

    for i, hourly_time_str in enumerate(hourly_times):
        hour_date = datetime.fromisoformat(hourly_time_str).date()
        if current_day is None:
            current_day = hour_date
            
        if hour_date == current_day:
            pressure = hourly_pressures[i]
            if pressure is not None:
                current_day_pressures.append(pressure)
        else:
            if current_day_pressures:
                daily_pressures.append(sum(current_day_pressures) / len(current_day_pressures))
            current_day = hour_date
            current_day_pressures = []
            pressure = hourly_pressures[i]
            if pressure is not None:
                current_day_pressures.append(pressure)
    
    if current_day_pressures: # Add the last day's average
        daily_pressures.append(sum(current_day_pressures) / len(current_day_pressures))

    average_weekly_pressure_hPa: float = round(sum(daily_pressures) / len(daily_pressures), 2) if daily_pressures else 0.0

    valid_sunshine_durations = [s for s in sunshine_durations if s is not None]
    total_sunshine_seconds = sum(valid_sunshine_durations)
    average_weekly_sunshine_hours: float = round((total_sunshine_seconds / len(valid_sunshine_durations)) / 3600, 2) if valid_sunshine_durations else 0.0

    all_temperatures = [t for t in temp_maxes + temp_mins if t is not None]
    weekly_min_temperature_celsius: float = min(all_temperatures) if all_temperatures else 0.0
    weekly_max_temperature_celsius: float = max(all_temperatures) if all_temperatures else 0.0

    days_with_precipitation = sum(1 for p_sum in precipitation_sums if p_sum is not None and p_sum > 0)
    weekly_weather_summary: str = "with precipitation" if days_with_precipitation >= 4 else "without precipitation"

    return WeeklySummary(
        average_weekly_pressure_hPa=average_weekly_pressure_hPa,
        average_weekly_sunshine_hours=average_weekly_sunshine_hours,
        weekly_min_temperature_celsius=weekly_min_temperature_celsius,
        weekly_max_temperature_celsius=weekly_max_temperature_celsius,
        weekly_weather_summary=weekly_weather_summary,
    )

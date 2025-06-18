from typing import Any, cast
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from app import OpenMeteoResponse, app
from fastapi import HTTPException

MOCK_OPEN_METEO_FORECAST_DATA: OpenMeteoResponse = {
    "latitude": 52.52,
    "longitude": 13.419998,
    "generationtime_ms": 0.3270149230957031,
    "utc_offset_seconds": 7200,
    "timezone": "Europe/Berlin",
    "timezone_abbreviation": "CEST",
    "elevation": 38.0,
    "daily_units": {
        "time": "iso8601",
        "weather_code": "wmo code",
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
        "sunshine_duration": "s",
    },
    "daily": {
        "time": [
            (date(2025, 6, 18) + timedelta(days=i)).isoformat() for i in range(7)
        ],
        "weather_code": [0, 1, 3, 61, 63, 80, 95],
        "temperature_2m_max": [15.0, 16.5, 17.0, 12.0, 10.0, 14.5, 13.0],
        "temperature_2m_min": [5.0, 6.0, 7.5, 8.0, 7.0, 5.5, 4.0],
        "sunshine_duration": [36000.0, 28800.0, 21600.0, 14400.0, 7200.0, 28800.0, 18000.0],
        "precipitation_sum": [0.0, 0.0, 0.0, 5.0, 10.0, 0.0, 0.0]
    },
    "hourly_units": {
        "time": "iso8601",
        "pressure_msl": "hPa"
    },
    "hourly": {
        "time": [
            (datetime(2025, 6, 18, 0, 0, 0) + timedelta(hours=i)).isoformat() for i in range(7 * 24)
        ],
        "pressure_msl": [
            1012.0 + i * 0.1 for i in range(7 * 24)
        ]
    }
}

MOCK_OPEN_METEO_SUMMARY_DATA: dict[str, Any] = {
    **MOCK_OPEN_METEO_FORECAST_DATA,
    "daily": {
        "time": [
            (date(2025, 6, 18) + timedelta(days=i)).isoformat() for i in range(7)
        ],
        "weather_code": [0, 1, 3, 61, 63, 80, 95],
        "temperature_2m_max": [15.0, 16.5, 17.0, 12.0, 10.0, 14.5, 13.0],
        "temperature_2m_min": [5.0, 6.0, 7.5, 8.0, 7.0, 5.5, 4.0],
        "sunshine_duration": [36000.0, 28800.0, 21600.0, 14400.0, 7200.0, 28800.0, 18000.0],
        "precipitation_sum": [0.0, 0.0, 0.0, 5.0, 10.0, 0.0, 0.0]
    }
}

MOCK_OPEN_METEO_SUMMARY_DATA_WITH_PRECIPITATION: dict[str, Any] = {
    **MOCK_OPEN_METEO_FORECAST_DATA,
    "daily": {
        "time": [
            (date(2025, 6, 18) + timedelta(days=i)).isoformat() for i in range(7)
        ],
        "weather_code": [61, 63, 65, 66, 67, 80, 0],
        "temperature_2m_max": [15.0, 16.5, 17.0, 12.0, 10.0, 14.5, 13.0],
        "temperature_2m_min": [5.0, 6.0, 7.5, 8.0, 7.0, 5.5, 4.0],
        "sunshine_duration": [36000.0, 28800.0, 21600.0, 14400.0, 7200.0, 28800.0, 18000.0],
        "precipitation_sum": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 0.0]
    }
}

@patch('app.fetch_open_meteo_data_internal')
def test_get_daily_forecast_success(mock_fetch: MagicMock):
    mock_fetch.return_value = MOCK_OPEN_METEO_FORECAST_DATA

    client = TestClient(app)
    response = client.get("/forecast?latitude=52.52&longitude=13.41")

    assert response.status_code == 200
    forecasts: list[dict[str, float | int | str]] = cast(list[dict[str, float | int | str]], response.json())
    assert isinstance(forecasts, list)
    assert len(forecasts) == 7

    first_day: dict[str, float | int | str] = forecasts[0]
    today: str = date(2025, 6, 18).isoformat()
    assert first_day["date"] == today
    assert first_day["weather_code"] == 0
    assert first_day["temperature_min_celsius"] == 5.0
    assert first_day["temperature_max_celsius"] == 15.0
    assert first_day["estimated_energy_kwh"] == 5.0

    last_day: dict[str, float | int | str] = forecasts[6]
    day_7: str = (date(2025, 6, 18) + timedelta(days=6)).isoformat()
    assert last_day["date"] == day_7
    assert last_day["weather_code"] == 95
    assert last_day["temperature_min_celsius"] == 4.0
    assert last_day["temperature_max_celsius"] == 13.0
    assert last_day["estimated_energy_kwh"] == 2.5


@patch('app.fetch_open_meteo_data_internal')
def test_get_daily_forecast_api_error(mock_fetch: MagicMock):
    mock_fetch.side_effect = HTTPException(status_code=500, detail="Error response from Open-Meteo API: Internal Server Error from external API")

    client = TestClient(app)
    response = client.get("/forecast?latitude=52.52&longitude=13.41")

    assert response.status_code == 500
    assert "Error response from Open-Meteo API" in response.json()["detail"]


@patch('app.fetch_open_meteo_data_internal')
def test_get_daily_forecast_network_error(mock_fetch: MagicMock):
    mock_fetch.side_effect = HTTPException(status_code=500, detail="Error connecting to Open-Meteo API, possibly a network issue.")

    client = TestClient(app)
    response = client.get("/forecast?latitude=52.52&longitude=13.41")

    assert response.status_code == 500
    assert "Error connecting to Open-Meteo API" in response.json()["detail"]


def test_get_daily_forecast_invalid_latitude():
    client = TestClient(app)
    response = client.get("/forecast?latitude=91.0&longitude=13.41")
    assert response.status_code == 422


@patch('app.fetch_open_meteo_data_internal')
def test_get_daily_forecast_missing_data_from_api(mock_fetch: MagicMock):
    mock_data: dict[str, Any] = {
        "latitude": 52.52,
        "longitude": 13.419998,
        "daily": {
            "time": [(date(2025, 6, 18)).isoformat()],
            "weather_code": [cast(Any, None)],
            "temperature_2m_max": [15.0],
            "temperature_2m_min": [5.0],
            "sunshine_duration": [36000.0]
        }
    }
    mock_fetch.return_value = mock_data

    client = TestClient(app)
    response = client.get("/forecast?latitude=52.52&longitude=13.41")

    assert response.status_code == 200
    assert len(response.json()) == 0


@patch('app.fetch_open_meteo_data_internal')
def test_get_weekly_summary_success(mock_fetch: MagicMock):
    mock_fetch.return_value = MOCK_OPEN_METEO_SUMMARY_DATA

    client = TestClient(app)
    response = client.get("/summary?latitude=52.52&longitude=13.41")

    assert response.status_code == 200
    summary: dict[str, float | str] = cast(dict[str, float | str], response.json())
    assert isinstance(summary, dict)

    expected_daily_pressures: list[float] = []
    hourly_data: dict[str, Any] = MOCK_OPEN_METEO_SUMMARY_DATA["hourly"]
    hourly_pressures_mock: list[float | int | None] = cast(list[float | int | None], hourly_data["pressure_msl"])
    hourly_times_mock: list[str] = cast(list[str], hourly_data["time"])

    current_day_test: date | None = None
    current_day_pressures_test: list[float] = []

    for i, hourly_time_str in enumerate(hourly_times_mock):
        hour_date_test: date = datetime.fromisoformat(hourly_time_str).date()
        pressure_test: float | int | None = hourly_pressures_mock[i]

        if current_day_test is None:
            current_day_test = hour_date_test
            
        if hour_date_test == current_day_test:
            if pressure_test is not None:
                current_day_pressures_test.append(float(pressure_test))
        else:
            if current_day_pressures_test:
                expected_daily_pressures.append(sum(current_day_pressures_test) / len(current_day_pressures_test))
            current_day_test = hour_date_test
            current_day_pressures_test = []
            if pressure_test is not None:
                current_day_pressures_test.append(float(pressure_test))
                
    if current_day_pressures_test:
        expected_daily_pressures.append(sum(current_day_pressures_test) / len(current_day_pressures_test))

    expected_avg_pressure: float = round(sum(expected_daily_pressures) / len(expected_daily_pressures), 2) if expected_daily_pressures else 0.0

    assert summary["average_weekly_pressure_hPa"] == expected_avg_pressure

    daily_data: dict[str, Any] = MOCK_OPEN_METEO_SUMMARY_DATA["daily"]
    sunshine_durations_raw: list[float | None] = cast(list[float | None], daily_data["sunshine_duration"])
    valid_sunshine_durations: list[float] = [float(s) for s in sunshine_durations_raw if s is not None]
    
    expected_avg_sunshine_hours: float = round((sum(valid_sunshine_durations) / len(valid_sunshine_durations)) / 3600, 2) if valid_sunshine_durations else 0.0
    assert summary["average_weekly_sunshine_hours"] == expected_avg_sunshine_hours

    temp_max_raw: list[float | None] = cast(list[float | None], daily_data["temperature_2m_max"])
    temp_min_raw: list[float | None] = cast(list[float | None], daily_data["temperature_2m_min"])

    all_temps: list[float] = [
        float(t) for t in temp_max_raw if t is not None
    ] + [
        float(t) for t in temp_min_raw if t is not None
    ]
    assert summary["weekly_min_temperature_celsius"] == min(all_temps)
    assert summary["weekly_max_temperature_celsius"] == max(all_temps)

    assert summary["weekly_weather_summary"] == "without precipitation"


@patch('app.fetch_open_meteo_data_internal')
def test_get_weekly_summary_with_precipitation(mock_fetch: MagicMock):
    mock_fetch.return_value = MOCK_OPEN_METEO_SUMMARY_DATA_WITH_PRECIPITATION

    client = TestClient(app)
    response = client.get("/summary?latitude=52.52&longitude=13.41")

    assert response.status_code == 200
    summary: dict[str, str] = cast(dict[str, str], response.json())
    assert summary["weekly_weather_summary"] == "with precipitation"


@patch('app.fetch_open_meteo_data_internal')
def test_get_weekly_summary_api_error(mock_fetch: MagicMock):
    mock_fetch.side_effect = HTTPException(status_code=403, detail="Error response from Open-Meteo API: Forbidden")

    client = TestClient(app)
    response = client.get("/summary?latitude=52.52&longitude=13.41")

    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


@patch('app.fetch_open_meteo_data_internal')
def test_get_weekly_summary_network_error(mock_fetch: MagicMock):
    mock_fetch.side_effect = HTTPException(status_code=500, detail="Error connecting to Open-Meteo API, possibly a network issue.")

    client = TestClient(app)
    response = client.get("/summary?latitude=52.52&longitude=13.41")

    assert response.status_code == 500
    assert "Error connecting to Open-Meteo API" in response.json()["detail"]


def test_get_weekly_summary_invalid_longitude():
    client = TestClient(app)
    response = client.get("/summary?latitude=52.52&longitude=181.0")
    assert response.status_code == 422

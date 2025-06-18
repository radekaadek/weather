<script lang="ts">
    import { onMount } from 'svelte';
    import type { Map, Marker, Icon } from 'leaflet';

    import 'leaflet/dist/leaflet.css';
    import iconUrl from 'leaflet/dist/images/marker-icon.png';
    import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
    import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

    import DarkModeToggle from './DarkModeToggle.svelte';

    const DEFAULT_LATITUDE = 52.23;
    const DEFAULT_LONGITUDE = 21.01;

    let darkMode: boolean | null = null;

    interface DailyForecast {
        date: string;
        weather_code: number;
        temperature_min_celsius: number;
        temperature_max_celsius: number;
        estimated_energy_kwh: number;
    }

    interface WeeklySummary {
        average_weekly_pressure_hPa: number;
        average_weekly_sunshine_hours: number;
        weekly_min_temperature_celsius: number;
        weekly_max_temperature_celsius: number;
        weekly_weather_summary: string;
    }

    let latitude: number | null = null;
    let longitude: number | null = null;
    // let latitude: number = 52.23;
    // let longitude: number = 21.01;

    let mapInstance: Map | null = null;
    let markerInstance: Marker | null = null;

    let forecastData: DailyForecast[] | null = null;
    let summaryData: WeeklySummary | null = null;
    let isLoading: boolean = false;
    let error: string | null = null;

    const API_BASE_URL: string = 'https://weather-2twl.onrender.com';

    const weatherIcons: { [key: number]: string } = {
        0: '☀️', 1: '🌤️', 2: '🌥️', 3: '☁️', 45: '🌫️', 48: '🌫️',
        51: '🌦️', 53: '🌦️', 55: '🌦️', 61: '🌧️', 63: '🌧️', 65: '🌧️',
        71: '❄️', 73: '❄️', 75: '❄️', 80: '🌧️', 81: '🌧️', 82: '🌧️',
        95: '⛈️', 96: '⛈️', 99: '⛈️'
    };

    function formatDate(dateString: string): string {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('pl-PL', {
            weekday: 'long',
            day: 'numeric',
            month: 'short'
        }).format(date);
    }

    async function getWeatherData(): Promise<void> {
        if (latitude === null || longitude === null) {
          return;
        }
        isLoading = true;
        error = null;
        forecastData = null;
        summaryData = null;
        if (latitude === null || longitude === null || latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
            error = "Nieprawidłowe współrzędne geograficzne.";
            isLoading = false;
            return;
        }
        try {
            const forecastUrl = `${API_BASE_URL}/forecast?latitude=${latitude}&longitude=${longitude}`;
            const summaryUrl = `${API_BASE_URL}/summary?latitude=${latitude}&longitude=${longitude}`;
            const [forecastResponse, summaryResponse] = await Promise.all([
                fetch(forecastUrl),
                fetch(summaryUrl)
            ]);
            if (!forecastResponse.ok || !summaryResponse.ok) {
                const errorSource = !forecastResponse.ok ? forecastResponse : summaryResponse;
                const errorDetails = await errorSource.json();
                throw new Error(`Błąd API: ${errorDetails.detail || 'Nieznany błąd serwera'}`);
            }
            forecastData = await forecastResponse.json();
            summaryData = await summaryResponse.json();
        } catch (e: any) {
            console.error('Błąd pobierania danych:', e);
            error = e.message || 'Nie udało się połączyć z serwerem. Upewnij się, że backend jest uruchomiony.';
        } finally {
            isLoading = false;
        }
    }

    onMount(async () => {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        darkMode = true;
        document.body.classList.add('dark');
      }
      let elem = document.getElementById('main-div');
      if (elem) {
        elem.style.display = 'block';
      }
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition((position) => {
          latitude = position.coords.latitude;
          longitude = position.coords.longitude;
          markerInstance?.setLatLng([latitude, longitude]);
        });
      }
      if (latitude === null || longitude === null) {
        latitude = DEFAULT_LATITUDE;
        longitude = DEFAULT_LONGITUDE;
      }
      const L = await import('leaflet')

      const defaultIcon: Icon = L.icon({
          iconUrl: iconUrl,
          iconRetinaUrl: iconRetinaUrl,
          shadowUrl: shadowUrl,
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          tooltipAnchor: [16, -28],
          shadowSize: [41, 41]
      });
      L.Marker.prototype.options.icon = defaultIcon;

      const mapContainer = document.getElementById('map-container');
      if (mapContainer) {
        mapInstance = L.map(mapContainer).setView([latitude, longitude], 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(mapInstance);

        markerInstance = L.marker([latitude, longitude], { draggable: true }).addTo(mapInstance);

        mapInstance.on('click', (e) => {
            const newCoords = e.latlng;
            latitude = newCoords.lat;
            longitude = newCoords.lng;
            markerInstance?.setLatLng(newCoords);
            getWeatherData();
        });

        markerInstance.on('drag', (e) => {
            const newCoords = e.target.getLatLng();
            latitude = newCoords.lat;
            longitude = newCoords.lng;
        });

        markerInstance.on('dragend', (e) => {
          const newCoords = e.target.getLatLng();
          latitude = newCoords.lat;
          longitude = newCoords.lng;
          getWeatherData();
        });
        getWeatherData();
      }
    });
</script>

<svelte:head>
    <title>Prognoza Pogody z Mapą</title>
</svelte:head>

<div id="main-div">
  <main class="container">
    <div class="topright-corner">
      <DarkModeToggle darkMode={darkMode} />
    </div>

    <header>
      <h1>☀️ Prognoza Pogody i Energii Słonecznej</h1>
      <p>Kliknij na mapę lub przeciągnij marker, aby wybrać lokalizację i zobaczyć prognozę.</p>
    </header>

    <div class="map-section">
      <div id="map-container" class="map-container"></div>
      <div class="coords-display">
        <span>Szerokość: <strong>{latitude ? latitude.toFixed(4): "-"}</strong></span>
        <span>Długość: <strong>{longitude ? longitude.toFixed(4): "-"}</strong></span>
      </div>
    </div>

    {#if error}
      <div class="error-box">
        <p><strong>Wystąpił błąd:</strong> {error}</p>
      </div>
    {/if}

    {#if isLoading}
      <div class="loader"></div>
    {/if}

    {#if !isLoading && !error && forecastData && summaryData}
      <div class="results-grid">
        <section class="summary-card">
          <h2>Podsumowanie Tygodnia</h2>
          <p class="summary-weather-info">
            Tydzień zapowiada się <strong>{summaryData.weekly_weather_summary}</strong>.
          </p>
          <ul>
            <li>
              <span>🌡️ Temp. Ekstremalne:</span>
              <strong>
                {summaryData.weekly_min_temperature_celsius.toFixed(1)}°C / {summaryData.weekly_max_temperature_celsius.toFixed(1)}°C
              </strong>
            </li>
            <li>
              <span>💨 Średnie ciśnienie:</span>
              <strong>{summaryData.average_weekly_pressure_hPa.toFixed(1)} hPa</strong>
            </li>
            <li>
              <span>☀️ Średnie nasłonecznienie:</span>
              <strong>{summaryData.average_weekly_sunshine_hours.toFixed(1)} godz./dzień</strong>
            </li>
          </ul>
        </section>

        <section class="forecast-section">
          <h2>Prognoza na 7 dni</h2>
          <div class="forecast-grid">
            {#each forecastData as day (day.date)}
              <div class="day-card">
                <div class="date">{formatDate(day.date)}</div>
                <div class="weather-icon">{weatherIcons[day.weather_code] || '❓'}</div>
                <div class="temp">
                  <span class="temp-max">{day.temperature_max_celsius.toFixed(1)}°C</span>
                  <span class="temp-min">{day.temperature_min_celsius.toFixed(1)}°C</span>
                </div>
                <div class="energy">
                  <span class="energy-icon">⚡</span>
                  <span>{day.estimated_energy_kwh.toFixed(2)} kWh</span>
                </div>
              </div>
            {/each}
          </div>
        </section>
      </div>
    {/if}
  </main>
</div>

<style>

  #main-div {
    display: none;
  }

  .topright-corner {
    padding-right: 0.5rem;
    padding-left: 0.5rem;
    margin: auto;
    padding-top: 0rem;
    justify-content: flex-end;
    display: flex;
    float: right;
  }

  :global(body) {
    background-color: var(--bg-color);
    transition: 0.2s;
    margin: 0;
    padding: 0;
  }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    .container { font-family: 'Inter', sans-serif; background-color: var(--card-bg); color: var(--text-color); line-height: 1.6; }
    .container { margin: auto; padding: 1rem; margin-bottom: 1rem; margin-top: 2rem; }
    header { text-align: center; margin-bottom: 2rem; }
    header h1 { font-size: 2.25rem; margin-bottom: 0.5rem; color: var(--title-color); }
    header p { color: var(--text-secondary); font-size: 1.1rem; }

    .map-section {
        margin-bottom: 2rem;
        background-color: var(--card-bg);
        border-radius: 0.75rem;
        box-shadow: var(--shadow);
        padding: 1rem;
    }

    .map-container {
        height: 400px;
        width: 100%;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
        background-color: #e2e8f0;
    }
  :global(body.dark) .map-container { background-color: var(--card-bg); }
    
    .coords-display {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        padding: 0.5rem;
        background-color: var(--bg-color);
        border-radius: 0.5rem;
        color: var(--text-secondary);
    }
  :global(body.dark) .coords-display {
      background-color: #2d3748;
      color: var(--text-secondary);
  }

    .coords-display strong {
        color: var(--text-color);
        font-weight: 500;
    }

  .error-box {
    background-color: var(--error-bg);
    color: var(--error-text);
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 2rem 0;
    text-align: center;
  }

  .loader {
      border: 5px solid #f3f3f3;
      border-top: 5px solid var(--primary-color);
      border-radius: 50%;
      width: 50px;
      height: 50px;
      animation: spin 1s linear infinite;
      margin: 2rem auto;
  }
  :global(body.dark) .loader {
    border-color: #4a5568;
    border-top-color: var(--primary-color);
  }


  @keyframes spin {
      0% {
          transform: rotate(0deg);
      }
      100% {
          transform: rotate(360deg);
      }
  }

  .results-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
  }

  @media (min-width: 768px) {
      .results-grid {
          grid-template-columns: 300px 1fr;
          align-items: start;
      }
  }

  .summary-card,
  .forecast-section {
      background-color: var(--card-bg);
      padding: 1.5rem;
      border-radius: 0.75rem;
      box-shadow: var(--shadow);
  }

  .summary-card h2,
  .forecast-section h2 {
      margin-bottom: 1.5rem;
      font-size: 1.25rem;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 0.75rem;
  }

  .summary-card .summary-weather-info {
      text-align: center;
      margin-bottom: 1.5rem;
      font-size: 1.1rem;
      color: var(--text-secondary);
  }

  .summary-card .summary-weather-info strong {
      color: var(--text-color);
      font-weight: 500;
  }

  .summary-card ul {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 1rem;
  }

  .summary-card li {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 1rem;
      color: var(--text-secondary);
  }

  .summary-card li strong {
      color: var(--text-color);
      font-weight: 500;
  }

  .forecast-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 1rem;
  }

  .day-card {
      border: 1px solid var(--border-color);
      border-radius: 0.75rem;
      padding: 1rem;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .day-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  }
  :global(body.dark) .day-card:hover {
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.2);
  }


  .day-card .date {
      font-weight: 500;
      font-size: 0.9rem;
      text-transform: capitalize;
  }

  .day-card .weather-icon {
      font-size: 3rem;
      margin: 0.5rem 0;
  }

  .day-card .temp {
      font-size: 1.1rem;
      font-weight: 500;
      display: flex;
      justify-content: center;
      gap: 0.75rem;
  }

  .day-card .temp-max {
      color: var(--text-color);
  }

  .day-card .temp-min {
      color: var(--text-secondary);
  }

  .day-card .energy {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.25rem;
      font-size: 0.9rem;
      background-color: var(--energy-bg);
      color: var(--energy-text);
      padding: 0.25rem 0.5rem;
      border-radius: 999px;
      margin-top: 0.5rem;
      font-weight: 500;
  }
  
  :global(body) {
    --bg-color: #f0f4f8;
    --card-bg: #ffffff;
    --text-color: #1e293b;
    --title-color: #0f172a;
    --text-secondary: #475569;
    --primary-color: #3b82f6;
    --primary-hover: #2563eb;
    --border-color: #e2e8f0;
    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --error-bg: #fee2e2;
    --error-text: #b91c1c;
        --energy-bg: #fefce8;
        --energy-text: #a16207;
  }


  /* Dark Mode Styles */
  :global(body.dark) {
      --bg-color: #1a202c;
      --card-bg: #2d3748;
      --text-color: #e2e8f0;
      --text-secondary: #a0aec0;
      --primary-color: #63b3ed;
      --primary-hover: #4299e1;
      --border-color: #4a5568;
      --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.2);
      --error-bg: #4c0519;
      --error-text: #fecaca;
      --energy-bg: #3a3a2e;
      --energy-text: #f6e05e;
      --title-color: #8d51ff;
  }
</style>

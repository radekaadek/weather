<script lang="ts">
  import { onMount } from 'svelte';
  import type { Map, Marker, Icon } from 'leaflet';

  import 'leaflet/dist/leaflet.css';
  import iconUrl from 'leaflet/dist/images/marker-icon.png';
  import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
  import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

  import DarkModeToggle from './DarkModeToggle.svelte';
  import MapSection from './MapSection.svelte';
  import WeatherSummary from './WeatherSummary.svelte';
  import DailyForecast from './DailyForecast.svelte';
  import ErrorMessage from './ErrorMessage.svelte';
  import LoadingSpinner from './LoadingSpinner.svelte';

  const DEFAULT_LATITUDE = 52.23;
  const DEFAULT_LONGITUDE = 21.01;
  const API_BASE_URL = 'https://weather-2twl.onrender.com';
  const LOCATION_ERROR_TIMEOUT = 4000;

  const weatherIcons: { [key: number]: string } = {
    0: '☀️', 1: '🌤️', 2: '🌥️', 3: '☁️', 45: '🌫️', 48: '🌫️',
    51: '🌦️', 53: '🌦️', 55: '🌦️', 61: '🌧️', 63: '🌧️', 65: '🌧️',
    71: '❄️', 73: '❄️', 75: '❄️', 80: '🌧️', 81: '🌧️', 82: '🌧️',
    95: '⛈️', 96: '⛈️', 99: '⛈️'
  };

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

  let darkMode: boolean | null = null;
  let latitude: number | null = null;
  let longitude: number | null = null;
  let mapInstance: Map | null = null;
  let markerInstance: Marker | null = null;
  let forecastData: DailyForecast[] | null = null;
  let summaryData: WeeklySummary | null = null;
  let isLoading: boolean = true;
  let apiError: string | null = null;
  let locationError: string | null = null;

  let mapContainerElement: HTMLDivElement;

  function areValidCoordinates(lat: number | null, lng: number | null): boolean {
    return lat !== null && lng !== null &&
           lat >= -90 && lat <= 90 &&
           lng >= -180 && lng <= 180;
  }

  function showLocationError(message: string): void {
    locationError = message;
    setTimeout(() => {
      locationError = null;
    }, LOCATION_ERROR_TIMEOUT);
  }

  async function getWeatherData(): Promise<void> {
    if (!areValidCoordinates(latitude, longitude)) {
      if (latitude !== null || longitude !== null) {
        apiError = "Nieprawidłowe współrzędne geograficzne.";
      }
      isLoading = false;
      return;
    }

    isLoading = true;
    apiError = null;
    forecastData = null;
    summaryData = null;

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
      apiError = e.message || 'Nie udało się połączyć z serwerem. Upewnij się, że backend jest uruchomiony.';
    } finally {
      isLoading = false;
    }
  }

  async function getCurrentLocation(): Promise<GeolocationPosition | null> {
    if (!("geolocation" in navigator)) {
      return null;
    }

    try {
      return await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
    } catch (e) {
      console.error(e);
      showLocationError("Wystąpił błąd podczas pobierania lokalizacji.");
      return null;
    }
  }

  function setDefaultLocation(): void {
    showLocationError("Nie można uzyskać lokalizacji.");
    latitude = DEFAULT_LATITUDE;
    longitude = DEFAULT_LONGITUDE;
  }

  function setupLeafletDefaults(L: any): void {
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
  }

  function initializeMap(L: any, mapContainer: Element): void {
    if (!areValidCoordinates(latitude, longitude)) return;

    mapInstance = L.map(mapContainer).setView([latitude!, longitude!], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(mapInstance);

    markerInstance = L.marker([latitude!, longitude!], { draggable: true }).addTo(mapInstance);
    setupMapEventListeners();
  }

  function setupMapEventListeners(): void {
    if (!mapInstance || !markerInstance) return;

    mapInstance.on('click', (e) => {
      const newCoords = e.latlng;
      updateCoordinates(newCoords.lat, newCoords.lng);
      markerInstance?.setLatLng(newCoords);
      getWeatherData();
    });

    markerInstance.on('drag', (e) => {
      const newCoords = e.target.getLatLng();
      updateCoordinates(newCoords.lat, newCoords.lng);
    });

    markerInstance.on('dragend', (e) => {
      const newCoords = e.target.getLatLng();
      updateCoordinates(newCoords.lat, newCoords.lng);
      getWeatherData();
    });
  }

  function updateCoordinates(lat: number, lng: number): void {
    latitude = lat;
    longitude = lng;
  }

  function initializeDarkMode(): void {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      darkMode = true;
      document.body.classList.add('dark');
    }
  }

  function showMainDiv(): void {
    const elem = document.getElementById('main-div');
    if (elem) {
      elem.style.display = 'block';
    }
  }

  onMount(async () => {
    initializeDarkMode();
    showMainDiv();

    const [L, position] = await Promise.all([
      import('leaflet'),
      getCurrentLocation()
    ]);

    setupLeafletDefaults(L);

    if (position) {
      latitude = position.coords.latitude;
      longitude = position.coords.longitude;
    } else {
      setDefaultLocation();
    }

    if (mapContainerElement) {
      initializeMap(L, mapContainerElement);
      getWeatherData();
    }
  });

  function handleMapClick(event: { detail: { lat: number, lng: number } }) {
    updateCoordinates(event.detail.lat, event.detail.lng);
    markerInstance?.setLatLng([event.detail.lat, event.detail.lng]);
    getWeatherData();
  }

  function handleMarkerDrag(event: { detail: { lat: number, lng: number } }) {
    updateCoordinates(event.detail.lat, event.detail.lng);
  }

  function handleMarkerDragEnd(event: { detail: { lat: number, lng: number } }) {
    updateCoordinates(event.detail.lat, event.detail.lng);
    getWeatherData();
  }
</script>

<svelte:head>
  <title>Prognoza Pogody z Mapą</title>
</svelte:head>

<div id="main-div">
  <main class="container">
    <div class="topright-corner">
      <DarkModeToggle {darkMode} />
    </div>

    <header>
      <h1>☀️ Prognoza Pogody i Energii Słonecznej</h1>
      <p>Kliknij na mapę lub przeciągnij marker, aby wybrać lokalizację i zobaczyć prognozę.</p>
    </header>

    {#if locationError}
      <ErrorMessage message={locationError} />
    {/if}

    <MapSection
      bind:mapContainerRef={mapContainerElement}
      bind:latitude
      bind:longitude
      on:mapClick={handleMapClick}
      on:markerDrag={handleMarkerDrag}
      on:markerDragEnd={handleMarkerDragEnd}
    />

    {#if apiError}
      <ErrorMessage message={apiError} />
    {/if}

    {#if isLoading}
      <LoadingSpinner />
    {/if}

    {#if !isLoading && !apiError && forecastData && summaryData}
      <div class="results-grid">
        <WeatherSummary {summaryData} />
        <DailyForecast {forecastData} {weatherIcons} />
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

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  .container {
    font-family: 'Inter', sans-serif;
    background-color: var(--card-bg);
    color: var(--text-color);
    line-height: 1.6;
    margin: auto;
    padding: 1rem;
    margin-bottom: 1rem;
    margin-top: 2rem;
  }

  header {
    text-align: center;
    margin-bottom: 2rem;
  }

  header h1 {
    font-size: 2.25rem;
    margin-bottom: 0.5rem;
    color: var(--title-color);
  }

  header p {
    color: var(--text-secondary);
    font-size: 1.1rem;
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

<script lang="ts">
	import { onMount } from 'svelte';

	// --- DEFINICJE TYPÓW ---
	// Typ dla pojedynczego dnia prognozy, zgodny z backendem
	interface DailyForecast {
		date: string;
		weather_code: number;
		temperature_min_celsius: number;
		temperature_max_celsius: number;
		estimated_energy_kwh: number;
	}

	// Typ dla podsumowania tygodniowego, zgodny z backendem
	interface WeeklySummary {
		average_weekly_pressure_hPa: number;
		average_weekly_sunshine_hours: number;
		weekly_min_temperature_celsius: number;
		weekly_max_temperature_celsius: number;
		weekly_weather_summary: string;
	}
	
	// --- ZMIENNE STANU ---
	// Domyślne współrzędne (np. dla Warszawy)
	let latitude: number = 52.23;
	let longitude: number = 21.01;

	// Otypowane zmienne stanu dla danych z API
	let forecastData: DailyForecast[] | null = null;
	let summaryData: WeeklySummary | null = null;
	let isLoading: boolean = false;
	let error: string | null = null;

	// Adres URL Twojego lokalnie uruchomionego backendu
	const API_BASE_URL: string = 'http://127.0.0.1:8000';

	// Mapa kodów pogodowych na ikony emoji dla lepszej wizualizacji
	// Zgodnie z dokumentacją Open-Meteo (WMO Weather interpretation codes)
	const weatherIcons: { [key: number]: string } = {
		0: '☀️', // Clear sky
		1: '🌤️', // Mainly clear
		2: '🌥️', // Partly cloudy
		3: '☁️', // Overcast
		45: '🌫️', // Fog
		48: '🌫️', // Depositing rime fog
		51: '🌦️', // Drizzle: Light
		53: '🌦️', // Drizzle: Moderate
		55: '🌦️', // Drizzle: Dense intensity
		61: '🌧️', // Rain: Slight
		63: '🌧️', // Rain: Moderate
		65: '🌧️', // Rain: Heavy intensity
		71: '❄️', // Snow fall: Slight
		73: '❄️', // Snow fall: Moderate
		75: '❄️', // Snow fall: Heavy intensity
		80: ' şiddetli yağmur 🌧️', // Rain showers: Slight
		81: ' şiddetli yağmur 🌧️', // Rain showers: Moderate
		82: ' şiddetli yağmur 🌧️', // Rain showers: Violent
		95: '⛈️', // Thunderstorm: Slight or moderate
		96: '⛈️', // Thunderstorm with slight hail
		99: '⛈️'  // Thunderstorm with heavy hail
	};

	/**
	 * Formatuje datę do bardziej przyjaznego formatu (np. "wtorek, 17 cze")
	 * @param dateString - Data w formacie ISO (YYYY-MM-DD)
	 * @returns Sformatowana data
	 */
	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('pl-PL', {
			weekday: 'long',
			day: 'numeric',
			month: 'short'
		}).format(date);
	}

	/**
	 * Asynchroniczna funkcja do pobierania danych pogodowych z backendu.
	 */
	async function getWeatherData(): Promise<void> {
		isLoading = true;
		error = null;
		forecastData = null;
		summaryData = null;

		// Walidacja inputów
		if (latitude === null || longitude === null || latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
			error = "Proszę podać poprawne współrzędne geograficzne.";
			isLoading = false;
			return;
		}

		try {
			const forecastUrl = `${API_BASE_URL}/forecast?latitude=${latitude}&longitude=${longitude}`;
			const summaryUrl = `${API_BASE_URL}/summary?latitude=${latitude}&longitude=${longitude}`;

			// Równoległe zapytania do obu endpointów
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

	// Automatyczne pobranie danych dla domyślnej lokalizacji po załadowaniu komponentu
	onMount(() => {
		getWeatherData();
	});
</script>

<svelte:head>
	<title>Prognoza Pogody</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
</svelte:head>

<main class="container">
	<header>
		<h1>☀️ Prognoza Pogody i Energii Słonecznej</h1>
		<p>Wprowadź szerokość i długość geograficzną, aby zobaczyć 7-dniową prognozę.</p>
	</header>

	<div class="form-container">
		<div class="input-group">
			<label for="latitude">Szerokość geograficzna</label>
			<input type="number" id="latitude" bind:value={latitude} placeholder="np. 52.23" step="0.01" />
		</div>
		<div class="input-group">
			<label for="longitude">Długość geograficzna</label>
			<input type="number" id="longitude" bind:value={longitude} placeholder="np. 21.01" step="0.01" />
		</div>
		<button on:click={getWeatherData} disabled={isLoading}>
			{isLoading ? 'Ładowanie...' : 'Pobierz Prognozę'}
		</button>
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
			<!-- Sekcja podsumowania tygodnia -->
			<section class="summary-card">
				<h2>Podsumowanie Tygodnia</h2>
                <p class="summary-weather-info">Tydzień zapowiada się <strong>{summaryData.weekly_weather_summary}</strong>.</p>
				<ul>
					<li>
						<span>🌡️ Temp. Ekstremalne:</span>
						<strong>{summaryData.weekly_min_temperature_celsius.toFixed(1)}°C / {summaryData.weekly_max_temperature_celsius.toFixed(1)}°C</strong>
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

			<!-- Sekcja prognozy dziennej -->
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

<style>
	:root {
		--bg-color: #f0f4f8;
		--card-bg: #ffffff;
		--text-color: #1e293b;
		--text-secondary: #475569;
		--primary-color: #3b82f6;
		--primary-hover: #2563eb;
		--border-color: #e2e8f0;
		--shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --error-bg: #fee2e2;
        --error-text: #b91c1c;
	}

	* {
		box-sizing: border-box;
		margin: 0;
		padding: 0;
	}

	body {
		font-family: 'Inter', sans-serif;
		background-color: var(--bg-color);
		color: var(--text-color);
		line-height: 1.6;
	}

	.container {
		max-width: 900px;
		margin: 2rem auto;
		padding: 1rem;
	}

	header {
		text-align: center;
		margin-bottom: 2rem;
	}

	header h1 {
		font-size: 2.25rem;
		margin-bottom: 0.5rem;
		color: #0f172a;
	}
    
    header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
    }

	.form-container {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		background-color: var(--card-bg);
		padding: 1.5rem;
		border-radius: 0.75rem;
		box-shadow: var(--shadow);
		margin-bottom: 2rem;
		align-items: flex-end;
	}

	.input-group {
		flex: 1 1 200px;
	}

	.input-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		font-size: 0.9rem;
	}

	.input-group input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid var(--border-color);
		border-radius: 0.5rem;
		font-size: 1rem;
		transition: border-color 0.2s, box-shadow 0.2s;
	}

	.input-group input:focus {
		outline: none;
		border-color: var(--primary-color);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
	}

	button {
		padding: 0.75rem 1.5rem;
		background-color: var(--primary-color);
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
		height: fit-content;
        margin-top: auto;
	}

	button:hover:not(:disabled) {
		background-color: var(--primary-hover);
	}

	button:disabled {
		background-color: #94a3b8;
		cursor: not-allowed;
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

	.summary-card, .forecast-section {
		background-color: var(--card-bg);
		padding: 1.5rem;
		border-radius: 0.75rem;
		box-shadow: var(--shadow);
	}

    .summary-card h2, .forecast-section h2 {
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
		grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
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
		background-color: #fefce8;
        color: #a16207;
		padding: 0.25rem 0.5rem;
		border-radius: 999px;
        margin-top: 0.5rem;
        font-weight: 500;
	}
</style>


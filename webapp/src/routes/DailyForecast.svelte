<script lang="ts">
  export let forecastData: Array<{
    date: string;
    weather_code: number;
    temperature_min_celsius: number;
    temperature_max_celsius: number;
    estimated_energy_kwh: number;
  }>;
  export let weatherIcons: { [key: number]: string };

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pl-PL', {
      weekday: 'long',
      day: 'numeric',
      month: 'short'
    }).format(date);
  }
</script>

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

<style>
  .forecast-section {
    background-color: var(--card-bg);
    padding: 1.5rem;
    border-radius: 0.75rem;
    box-shadow: var(--shadow);
  }

  .forecast-section h2 {
    margin-bottom: 1.5rem;
    font-size: 1.25rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.75rem;
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
</style>

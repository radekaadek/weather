<script lang="ts">
  export let summaryData: {
    average_weekly_pressure_hPa: number;
    average_weekly_sunshine_hours: number;
    weekly_min_temperature_celsius: number;
    weekly_max_temperature_celsius: number;
    weekly_weather_summary: string;
  };
</script>

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

<style>
  .summary-card {
    background-color: var(--card-bg);
    padding: 1.5rem;
    border-radius: 0.75rem;
    box-shadow: var(--shadow);
  }

  .summary-card h2 {
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
</style>

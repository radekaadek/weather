<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let latitude: number | null;
  export let longitude: number | null;
  export let mapContainerRef: HTMLDivElement;

  const dispatch = createEventDispatcher();
</script>

<div class="map-section">
  <div bind:this={mapContainerRef} class="map-container"></div>
  <div class="coords-display">
    <span>Szerokość: <strong>{latitude ? latitude.toFixed(4) : "-"}</strong></span>
    <span>Długość: <strong>{longitude ? longitude.toFixed(4) : "-"}</strong></span>
  </div>
</div>

<style>
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

  :global(body.dark) .map-container {
    background-color: var(--card-bg);
  }

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
</style>

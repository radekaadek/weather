<script lang="ts">
  export let message: string;
</script>

<div class="error-box">
  <p><strong>Wystąpił błąd:</strong> {message}</p>
</div>

<style>
  .error-box {
    background-color: var(--error-bg);
    color: var(--error-text);
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 2rem 0;
    text-align: center;
  }
</style>

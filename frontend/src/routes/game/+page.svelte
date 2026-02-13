<script lang="ts">
  import GameSession from "$lib/components/GameSession.svelte";
  let { data } = $props();
  // console.log(data);
</script>

<div class="container mx-auto px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <h1 class="mb-4 text-2xl font-bold sm:mb-0 sm:text-3xl lg:text-4xl">Game sessions:</h1>
    {#if data.authenticatedUser && data.authenticatedUser.scopes?.includes("games:create")}
      <!-- {#if data.authenticatedUser} -->
      <a
        href="/game/create"
        class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none sm:px-6 sm:py-3 sm:text-base"
        >Create Session</a
      >
    {/if}
  </div>
  {#each [...data.game_sessions].reverse() as session}
    <GameSession
      {session}
      authenticatedUser={data.authenticatedUser
        ? { ...data.authenticatedUser, scopes: data.authenticatedUser.scopes ?? [] }
        : undefined}
    />
  {/each}
</div>

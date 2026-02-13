<script lang="ts">
  import GameSession from "$lib/components/GameSession.svelte";
  let { data } = $props();
  // console.log(data);
</script>

<div class="container">
  <h1 class="text-4xl font-bold">Game sessions:</h1>

  {#each [...data.game_sessions].reverse() as session}
    <GameSession
      {session}
      authenticatedUser={data.authenticatedUser
        ? { ...data.authenticatedUser, scopes: data.authenticatedUser.scopes ?? [] }
        : undefined}
    />
  {/each}

  {#if data.authenticatedUser && data.authenticatedUser.scopes?.includes("games:create")}
    <!-- {#if data.authenticatedUser} -->
    <div class="mt-4">
      <a
        href="/game/create"
        class="rounded-md bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-800 lg:float-right"
        >Create Session</a
      >
    </div>
  {/if}
</div>

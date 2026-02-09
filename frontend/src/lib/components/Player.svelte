<script lang="ts">
  import { enhance } from "$app/forms";
  import type { components } from "$lib/api/v1";

  type Props = {
    player: components["schemas"]["GamePlayerPublic"];
    authenticatedUser?: components["schemas"]["UserMePublic"];
  };

  let { player, authenticatedUser }: Props = $props();
</script>

<div class="surface-2 rounded-lg p-4 transition-shadow hover:shadow-md">
  <div class="flex items-center justify-between gap-3">
    <!-- Player Info -->
    <a
      href="/game/{player.game_session_id}/player/{player.id}"
      class="min-w-0 flex-1 transition-colors hover:text-blue-600"
    >
      <div class="space-y-1">
        <h3 class="truncate text-sm font-semibold text-gray-900 sm:text-base dark:text-gray-100">
          {player.name}
        </h3>
        {#if player.team}
          <p class="truncate text-xs text-gray-600 sm:text-sm dark:text-gray-300">
            <span class="font-medium">Team:</span>
            {player.team.name}
          </p>
        {:else}
          <p class="text-xs text-gray-500 italic sm:text-sm dark:text-gray-400">No team assigned</p>
        {/if}
      </div>
    </a>

    <!-- Delete Button -->
    <form
      action="/game/{player.game_session_id}?/deletePlayer"
      method="POST"
      use:enhance
      class="shrink-0"
    >
      <input type="hidden" name="player_id" value={player.id} />
      <input type="hidden" name="game_session_id" value={player.game_session_id} />
      <button
        class="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none sm:px-4 sm:py-2 sm:text-sm"
        type="submit"
      >
        Delete
      </button>
    </form>
  </div>
</div>

<script lang="ts">
	import { enhance } from '$app/forms';
	import type { components } from '$lib/api/v1';

	type Props = {
		player: components['schemas']['GamePlayerPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};

	let { player, authenticatedUser }: Props = $props();
</script>

<div
	class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
>
	<div class="flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
		<!-- Player Info -->
		<a
			href="/game/{player.game_session_id}/player/{player.id}"
			class="flex-1 transition-colors hover:text-blue-600"
		>
			<div class="space-y-1">
				<h3 class="text-sm font-semibold text-gray-900 sm:text-base">{player.name}</h3>
				{#if player.team}
					<p class="text-xs text-gray-600 sm:text-sm">
						<span class="font-medium">Team:</span>
						{player.team.name}
					</p>
				{:else}
					<p class="text-xs italic text-gray-500 sm:text-sm">No team assigned</p>
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
				class="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 sm:px-4 sm:py-2"
				type="submit"
			>
				Delete
			</button>
		</form>
	</div>
</div>

<script lang="ts">
	import { enhance } from '$app/forms';
	import type { components } from '$lib/api/v1';

	type Props = {
		player: components['schemas']['GamePlayerPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};

	let { player, authenticatedUser }: Props = $props();
</script>

<div class="flex h-12 items-center justify-between rounded-md bg-gray-100 dark:bg-gray-800">
	<a href="/game/{player.game_session_id}/player/{player.id}" class="flex flex-auto pl-2">
		<p class="">{player.name}</p>
	</a>

	<!-- <a href="/" class="mr-2 flex rounded-md bg-blue-600 px-4 py-2 text-white">
		<p>Delete</p>
	</a> -->
	<form action="/game/{player.game_session_id}?/deletePlayer" method="POST" use:enhance>
		<input type="hidden" name="player_id" value={player.id} />
		<input type="hidden" name="game_session_id" value={player.game_session_id} />
		<button
			class="rounded-md bg-red-600 px-4 py-2 font-medium text-gray-300 hover:bg-red-900 hover:text-white"
			type="submit"
		>
			Delete
		</button>
	</form>
</div>

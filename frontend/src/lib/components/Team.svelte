<script lang="ts">
	import { enhance } from '$app/forms';
	import type { components } from '$lib/api/v1';

	type Props = {
		team: components['schemas']['GameTeamPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};

	let { team, authenticatedUser }: Props = $props();

	// get GameSession
</script>

<!-- {console.log(team)} -->

<!-- {JSON.stringify(team)} -->

<div class="flex h-12 items-center justify-between rounded-md bg-gray-100 dark:bg-gray-800">
	<a href="/game/{team.game_session_id}/team/{team.id}" class="flex flex-auto pl-2">
		<p class="">{team.name}</p>
	</a>

	<!-- <a href="/" class="mr-2 flex rounded-md bg-blue-600 px-4 py-2 text-white">
		<p>Delete</p>
	</a> -->
	<form action="/game?/delete" method="POST" use:enhance>
		<input type="hidden" name="team_id" value={team.id} />
		<input type="hidden" name="game_session_id" value={team.game_session_id} />
		<button
			class="rounded-md bg-red-600 px-4 py-2 font-medium text-gray-300 hover:bg-red-900 hover:text-white"
			type="submit"
		>
			Delete
		</button>
	</form>
</div>

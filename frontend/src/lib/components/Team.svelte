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

<div
	class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
>
	<div class="flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
		<!-- Team Info -->
		<a
			href="/game/{team.game_session_id}/team/{team.id}"
			class="flex-1 transition-colors hover:text-blue-600"
		>
			<div class="space-y-1">
				<h3 class="text-sm font-semibold text-gray-900 sm:text-base">{team.name}</h3>
				<p class="text-xs text-gray-500 sm:text-sm">Team</p>
			</div>
		</a>

		<!-- Delete Button -->
		<form
			action="/game/{team.game_session_id}?/deleteTeam"
			method="POST"
			use:enhance
			class="flex-shrink-0"
		>
			<input type="hidden" name="team_id" value={team.id} />
			<input type="hidden" name="game_session_id" value={team.game_session_id} />
			<button
				class="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 sm:px-4 sm:py-2"
				type="submit"
			>
				Delete
			</button>
		</form>
	</div>
</div>

<script lang="ts">
	import { enhance } from "$app/forms";
	import type { components } from "$lib/api/v1";

	type Props = {
		team: components["schemas"]["GameTeamPublic"];
		authenticatedUser?: components["schemas"]["UserPublic"];
	};

	let { team, authenticatedUser }: Props = $props();

	// get GameSession
</script>

<!-- {console.log(team)} -->

<!-- {JSON.stringify(team)} -->

<div class="surface-2 rounded-lg p-4 transition-shadow hover:shadow-md">
	<div class="flex items-center justify-between gap-3">
		<!-- Team Info -->
		<a
			href="/game/{team.game_session_id}/team/{team.id}"
			class="min-w-0 flex-1 transition-colors hover:text-blue-600"
		>
			<div class="space-y-1">
				<h3 class="truncate text-sm font-semibold text-gray-900 sm:text-base dark:text-gray-100">
					{team.name}
				</h3>
				<p class="text-xs text-gray-500 sm:text-sm dark:text-gray-400">Team</p>
			</div>
		</a>

		<!-- Delete Button -->
		<form
			action="/game/{team.game_session_id}?/deleteTeam"
			method="POST"
			use:enhance
			class="shrink-0"
		>
			<input type="hidden" name="team_id" value={team.id} />
			<input type="hidden" name="game_session_id" value={team.game_session_id} />
			<button
				class="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none sm:px-4 sm:py-2 sm:text-sm"
				type="submit"
			>
				Delete
			</button>
		</form>
	</div>
</div>

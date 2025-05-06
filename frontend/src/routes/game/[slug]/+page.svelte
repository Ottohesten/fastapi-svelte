<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	import Team from '$lib/components/Team.svelte';
	let { data } = $props();
	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});
</script>

<SuperDebug data={$form} />

<div class="container">
	<div>
		<h2 class="text-4xl font-bold">Players:</h2>
		{#if data.game_session.players.length === 0}
			<p>No players available.</p>
		{/if}
		{#each data.game_session.players as player}
			<div class="my-4 rounded-md bg-gray-100 p-4 dark:bg-gray-800">
				<p>{player.name}</p>
			</div>
		{/each}

		<!-- teams -->
		<h2 class="text-4xl font-bold">Teams:</h2>
		<div class="flex flex-col space-y-4">
			{#if data.game_session.teams.length === 0}
				<p>No teams available.</p>
			{/if}

			{#each data.game_session.teams as team}
				<Team {team} />
			{/each}
		</div>
		<div>
			<button
				type="submit"
				class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
				>Add Team</button
			>
		</div>
	</div>
</div>

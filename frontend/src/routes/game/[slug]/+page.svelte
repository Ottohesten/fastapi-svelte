<script lang="ts">
	import Team from '$lib/components/Team.svelte';
	let { data } = $props();
	console.log(data.game_session);
</script>

<div class="container">
	<div>
		<h2 class="text-4xl font-bold">Players:</h2>
		{#each data.game_session.players as player}
			<div class="my-4 rounded-md bg-gray-100 p-4 dark:bg-gray-800">
				<p>{player.name}</p>
			</div>
		{/each}

		<!-- teams -->
		<h2 class="text-4xl font-bold">Teams:</h2>
		{#each data.game_session.teams as team}
			<Team {team} />
		{/each}
	</div>
</div>

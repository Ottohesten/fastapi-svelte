<script lang="ts">
	let { data } = $props();
	// console.log(data);
</script>

<div class="container">
	<h1 class="text-4xl font-bold">Game sessions:</h1>

	{#each [...data.game_sessions].reverse() as session}
		<!-- temporary display until i create component -->
		<div class="my-4 rounded-md bg-gray-100 p-4 dark:bg-gray-800">
			<a href="/game/{session.id}">
				<p>Title: {session.title}</p>
				<p>Owner: {session.owner.email}</p>
			</a>
		</div>
	{/each}

	{#if data.authenticatedUser}
		<div class="mt-4">
			<a
				href="/game/create"
				class="rounded-md bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-800 lg:float-right"
				>Create Session</a
			>
		</div>
	{/if}
</div>

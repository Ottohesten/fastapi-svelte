<script lang="ts">
	import Recipe from '$lib/components/Recipe.svelte';
	let { data } = $props();
</script>

<!-- {console.log(form)} -->
<!-- {console.log(data)} -->

<div class="container">
	<h1 class="text-4xl font-bold">Recipes:</h1>

	{#each data.recipes as recipe}
		<!-- <a href="/recipes/{recipe.id}"><Recipe {recipe} user={data.user} /></a> -->
		{#if data.user}
			<Recipe {recipe} user={data.user} />
		{:else}
			<Recipe {recipe} />
		{/if}
	{/each}
	{#if data.user}
		<div class="mt-4">
			<a
				href="/recipes/create"
				class="rounded-md bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-800 lg:float-right"
				>Create</a
			>
		</div>
	{/if}
</div>

<!-- <form action="/recipes?/create" method="POST">
	<button
		type="submit"
		class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
	>
		submit
	</button>
</form> -->

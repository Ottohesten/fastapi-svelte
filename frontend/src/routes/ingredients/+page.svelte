<script lang="ts">
	import Ingredient from '$lib/components/Ingredient.svelte';
	let { data } = $props();
</script>

<!-- {JSON.stringify(data)} -->

<div class="container">
	<h1 class="text-4xl font-bold">Ingredients:</h1>

	{#each data.ingredients as ingredient}
		<Ingredient user={data.user} {ingredient} />
	{/each}
</div>

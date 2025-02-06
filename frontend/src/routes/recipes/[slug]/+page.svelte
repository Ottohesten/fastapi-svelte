<script lang="ts">
	import Recipe from '$lib/components/Recipe.svelte';
	let { data } = $props();
</script>

<!-- {JSON.stringify(data.authenticatedUser)} -->
<div class="container">
	<Recipe recipe={data.recipe} authenticatedUser={data.authenticatedUser ?? undefined} />
</div>

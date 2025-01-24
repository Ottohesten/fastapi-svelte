<script lang="ts">
	import Recipe from '$lib/components/Recipe.svelte';
	let { data } = $props();
</script>

<div class="container">
	<Recipe recipe={data.recipe} user={data.user} />
</div>

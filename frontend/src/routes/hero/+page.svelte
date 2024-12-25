<script lang="ts">
	import Hero from '$lib/components/Hero.svelte';
	let { data } = $props();
</script>

<h1 class="text-4xl font-bold">Hero</h1>

{#each data.heroes as hero}
	<a href="/hero/{hero.id}"><Hero {...hero} age={hero.age ?? 0} /></a>
{/each}

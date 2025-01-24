<script lang="ts">
	import Hero from '$lib/components/Hero.svelte';
	let { data } = $props();
</script>

<div class="container">
	<h1 class="text-4xl font-bold">Hero</h1>
	<Hero {...data.hero} age={data.hero.age ?? 0} />
</div>

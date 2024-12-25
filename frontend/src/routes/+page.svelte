<script lang="ts">
	import Hero from '$lib/components/Hero.svelte';
	let { data } = $props();

	// async function fetchData() {
	//     console.log("fetching data");
	//     const response = await fetch("http://localhost:8000/");
	//     const data = await response.json();
	//     console.log(data);
	//     return data;
	// }
</script>

<h1 class="text-3xl font-bold underline">Home</h1>

<!-- {JSON.stringify(data)} -->
{#each data.items as item}
	<Hero {...item} age={item.age ?? 0} />
{/each}

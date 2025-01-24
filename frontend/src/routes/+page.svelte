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

<div class="container">
	<h1 class="text-3xl font-bold underline">Home</h1>

	<!-- {JSON.stringify(data)} -->
	<!-- {#each data.items as item}
		<Hero {...item} age={item.age ?? 0} />
	{/each} -->

	<!-- {#if data.user}
		<div class="bg-green-500">
			<h1>Welcome {data.user.email}</h1>
		</div>
	{/if} -->

	{JSON.stringify(data.user)}
</div>

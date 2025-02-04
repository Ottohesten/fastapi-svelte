<script lang="ts">
	// import Hero from '$lib/components/Hero.svelte';
	import Tiptap from '$lib/components/Tiptap.svelte';
	let { data } = $props();

	// async function fetchData() {
	//     console.log("fetching data");
	//     const response = await fetch("http://localhost:8000/");
	//     const data = await response.json();
	//     console.log(data);''
	//     return data;
	// }
</script>

<!-- {JSON.stringify(data.user)} -->'
<!-- {console.timeStamp()} -->
<div class="prose">
	<Tiptap />
</div>
<div class="container">
	<!-- <h1 class="mb-4 text-center text-3xl font-bold underline">Internationale Border Fanger Regler</h1>
	<div>
		<ul class="mb-4 rounded-lg border border-gray-200 text-center font-medium">
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Man kan kun kalde bordet fanger på en person, dvs. ikke et "vi"
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Hvis man vil sige "aldrig alene" skal det være det første man siger, og det skal siges lige
				efter man er blevet fanget
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Man kan ikke blive bordet fanger på et citat
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Man kan ikke blive bordet fanger på at synge med på en sang
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Hvis man bryder en bordet fanger skylder man et øltårn i KB
			</li>
		</ul>
		<h1 class="mb-4 text-center text-3xl font-bold underline">Online bordet fanger regler</h1>
		<ul class="rounded-lg border border-gray-200 text-center font-medium">
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Du kan stadig blive fanget ved at skrive noget i en chat, hvorefter en anden skriver bordet
				fanger
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				For at sige aldrig alene på online bordet fanger, skal du svare "Aldrig alene" som den
				første besked efter.
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Tiden der må gå til at du stadig kan sige aldrig alene er max 30 minutter
			</li>
		</ul>
	</div> -->
</div>

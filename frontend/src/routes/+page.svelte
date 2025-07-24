<script lang="ts">
	import { Button, buttonVariants } from '$lib/components/ui/button/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';

	let { data } = $props();

	// async function fetchData() {
	//     console.log("fetching data");
	//     const response = await fetch("http://localhost:8000/");
	//     const data = await response.json();
	//     console.log(data);''
	//     return data;
	// }
</script>

<!-- {JSON.stringify(data.user)} -->
<!-- {console.timeStamp()} -->
<div class="container">
	<h1 class="mb-4 text-center text-3xl font-bold underline">Internationale Border Fanger Regler</h1>
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
	</div>
	<!-- <h1 class="mb-4 text-center text-3xl font-bold underline">Internationale Jinx Regler</h1>
	<div>
		<ul class="mb-4 rounded-lg border border-gray-200 text-center font-medium">
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Hvis 2 personer siger det samme ord på samme tid, så bliver den første der siger det jinxet
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Jinxet betyder at de ikke må sige noget for deres navn er blevet sagt af en vilkårlig person
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Jinx kan også ske online i form af en tekstbesked, hvor den første person skriver en
				sætning, og den anden person skriver det ummidelbart lige efter, og derefter skriver "Jinx".
				Derefter gælder der samme regel med at personen jinxet ikke må skrive noget i chatten før en
				anden skriver deres navn, ellers skal de gøre en straf person der jinxer bestemmer, med max
				værdi af samme som et tårn i kb.
			</li>
			<li class="rounded-t-lg border-b border-gray-200 py-2">
				Jinx kan ikke ske på et citat, eller en sang
			</li>
		</ul>
	</div> -->
</div>
<!-- <Dialog.Root>
	<Dialog.Trigger class={buttonVariants({ variant: 'outline' })}>Edit Profile</Dialog.Trigger>
	<Dialog.Content class="sm:max-w-[425px]">
		<Dialog.Header>
			<Dialog.Title>Edit profile</Dialog.Title>
			<Dialog.Description>
				Make changes to your profile here. Click save when you're done.
			</Dialog.Description>
		</Dialog.Header>
		<div class="grid gap-4 py-4">
			<div class="grid grid-cols-4 items-center gap-4">
				<Label for="name" class="text-right">Name</Label>
				<Input id="name" value="Pedro Duarte" class="col-span-3" />
			</div>
			<div class="grid grid-cols-4 items-center gap-4">
				<Label for="username" class="text-right">Username</Label>
				<Input id="username" value="@peduarte" class="col-span-3" />
			</div>
		</div>
		<Dialog.Footer>
			<Button type="submit">Save changes</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root> -->

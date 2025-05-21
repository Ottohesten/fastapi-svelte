<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	let { data } = $props();

	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});
</script>

<SuperDebug data={$form} />

<div class="container">
	<form method="POST" action="" enctype="multipart/form-data" use:enhance>
		<div class="">
			<label class="" for="title">Title</label>
			<input
				class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
				type="text"
				name="title"
				aria-invalid={$errors.title ? 'true' : undefined}
				bind:value={$form.title}
				{...$constraints.title}
				required
			/>
			{#if $errors.title}<span class="invalid">{$errors.title}</span>{/if}
		</div>
		<div>
			<h1 class="mt-5">Teams</h1>
			<hr />
		</div>
		{#each $form.teams as _, i}
			<div class="mt-5">
				Name
				<input
					class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
					type="text"
					data-invalid={$errors.teams?.[i]?.name}
					bind:value={$form.teams[i].name}
				/>
			</div>
		{/each}

		<div class="mt-5 flex space-x-2">
			<button
				type="button"
				class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
				onclick={() => ($form.teams = [...($form.teams ?? []), { name: '', players: [] }])}
				>Add Team</button
			>
			<button
				class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
				type="submit"
			>
				Submit
			</button>
		</div>

		<div class="mt-5"></div>
	</form>
</div>

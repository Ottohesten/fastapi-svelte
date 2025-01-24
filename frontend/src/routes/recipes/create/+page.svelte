<script lang="ts">
	import { superForm } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	let { data } = $props();
	// import { enhance } from '$app/forms';

	const { form, errors, message, constraints, enhance } = superForm(data.form);
</script>

<SuperDebug data={$form} />

<div class="mx-auto max-w-md">
	{#if $message}<h3 class="text-center text-2xl">{$message}</h3>{/if}
	<form method="POST" action="" use:enhance>
		<!-- <form action="/recipes?/create" method="POST" use:enhance> -->
		<!-- <form action="" method="POST" use:enhance> -->
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
		<div class="mt-5">
			<label class="" for="description">Description</label>
			<input
				class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
				type="text"
				name="description"
				aria-invalid={$errors.description ? 'true' : undefined}
				{...$constraints.description}
				bind:value={$form.description}
			/>
			{#if $errors.description}<span class="invalid">{$errors.description}</span>{/if}
		</div>
		<!-- <div class="mt-5">
			<label class="" for="description">Ingredients</label>
		</div> -->

		<div class="mt-5">
			<button
				class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
				type="submit"
			>
				Submit
			</button>
		</div>
	</form>
</div>

<style>
	.invalid {
		color: red;
	}
</style>

<script lang="ts">
	import { superForm } from "sveltekit-superforms";
	import { untrack } from "svelte";
	import { Field, Control, Label, FieldErrors } from "formsnap";
	import { Input } from "$lib/components/ui/input";
	import { Button } from "$lib/components/ui/button";

	let { data } = $props();

	const form = superForm(
		untrack(() => data.form),
		{
			dataType: "json"
		}
	);

	const { form: formData, errors, message, constraints, enhance } = form;
</script>

<!-- <SuperDebug data={$form} /> -->

<div class="container mx-auto max-w-2xl p-4">
	<form method="POST" action="" enctype="multipart/form-data" use:enhance class="space-y-6">
		{#if $message}
			<h3 class="text-center text-2xl text-red-500">{$message}</h3>
		{/if}

		<Field {form} name="title">
			<Control>
				{#snippet children({ props })}
					<Label>Title</Label>
					<Input {...props} bind:value={$formData.title} placeholder="Game session title" />
				{/snippet}
			</Control>
			<FieldErrors />
		</Field>

		<div>
			<h1 class="mt-6 mb-2 text-xl font-semibold">Teams</h1>
			<hr class="border-gray-200 dark:border-gray-800" />
		</div>

		{#each $formData.teams as _, i}
			<div
				class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800/50"
			>
				<Field {form} name="teams[{i}].name">
					<Control>
						{#snippet children({ props })}
							<Label>Team Name</Label>
							<Input
								{...props}
								bind:value={$formData.teams[i].name}
								placeholder="Enter team name"
							/>
						{/snippet}
					</Control>
					<FieldErrors />
				</Field>
			</div>
		{/each}

		<div class="flex gap-4">
			<Button
				variant="secondary"
				type="button"
				onclick={() => ($formData.teams = [...($formData.teams ?? []), { name: "", players: [] }])}
			>
				Add Team
			</Button>
			<Button type="submit">Submit</Button>
		</div>

		<div class="mt-5"></div>
	</form>
</div>

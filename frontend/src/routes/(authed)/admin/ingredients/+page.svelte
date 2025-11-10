<script lang="ts">
	let { data } = $props();
	import DataTable from '$lib/components/ui/data-table.svelte';
	import Button, { buttonVariants } from '$lib/components/ui/button/button.svelte';
	import { enhance } from '$app/forms';
	import { columns } from './columns.js';
	import { invalidateAll } from '$app/navigation';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { IngredientSchema } from '$lib/schemas/schemas.js';
	import { Field, Control, Label, FieldErrors } from 'formsnap';

	let open = $state(false);

	const form = superForm(data.ingredientCreateForm, {
		validators: zodClient(IngredientSchema),
		resetForm: true,
		onUpdated: ({ form }) => {
			if (form.valid && form.message) {
				open = false;
				invalidateAll();
			}
		}
	});

	const { form: formData, enhance: formEnhance, errors, message } = form;
</script>

<div class="mx-auto max-w-7xl">
	<div class="mb-4 flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold">Ingredients</h1>
			<p class="mt-1 text-sm text-gray-600 dark:text-gray-300">
				Manage ingredients and their nutritional information
			</p>
		</div>
		<Dialog.Root bind:open>
			<Dialog.Trigger class={buttonVariants()}>Add Ingredient</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[425px]">
				<Dialog.Header>
					<Dialog.Title>Add New Ingredient</Dialog.Title>
					<Dialog.Description>Add a new ingredient to the database.</Dialog.Description>
				</Dialog.Header>
				<form method="POST" action="?/create" use:formEnhance class="space-y-4">
					{#if $message}
						<div class="rounded-md border border-red-200 bg-red-50 p-3">
							<p class="text-sm text-red-600">
								{$message}
							</p>
						</div>
					{/if}
					<div class="space-y-4">
						<Field {form} name="title">
							<Control>
								{#snippet children({ props })}
									<Label>Name</Label>
									<Input
										{...props}
										type="text"
										bind:value={$formData.title}
										placeholder="Enter ingredient name"
										class="mt-2"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>
						<Field {form} name="calories">
							<Control>
								{#snippet children({ props })}
									<Label>Calories (per 100g)</Label>
									<Input
										{...props}
										type="number"
										bind:value={$formData.calories}
										placeholder="Enter calories"
										class="mt-2"
										min="0"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>
					</div>
					<Dialog.Footer>
						<Button type="submit">Add Ingredient</Button>
					</Dialog.Footer>
				</form>
			</Dialog.Content>
		</Dialog.Root>
	</div>

	{#if $message}
		<div class="mb-4 rounded-md border border-green-200 bg-green-50 p-3">
			<p class="text-sm text-green-600">{$message}</p>
		</div>
	{/if}

	<DataTable
		data={data.ingredients}
		{columns}
		searchColumn="title"
		searchPlaceholder="Filter ingredients..."
	/>
</div>

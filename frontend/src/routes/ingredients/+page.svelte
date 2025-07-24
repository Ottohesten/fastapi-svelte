<script lang="ts">
	import Ingredient from '$lib/components/Ingredient.svelte';

	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { superForm, type SuperValidated, type Infer } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import SuperDebug from 'sveltekit-superforms';
	import { Field, Control, Label, Description, FieldErrors } from 'formsnap';
	import { Input } from '$lib/components/ui/input/index.js';
	import { IngredientSchema } from '$lib/schemas/schemas.js';

	let { data } = $props();

	let dialogOpen = $state(false);

	const form = superForm(data.ingredientCreateForm, {
		validators: zodClient(IngredientSchema),
		resetForm: true,
		onUpdated: ({ form }) => {
			console.log('Form updated:', {
				valid: form.valid,
				message: form.message,
				errors: form.errors
			});
			if (form.valid && form.message) {
				// console.log('Closing dialog...');
				dialogOpen = false;
			}
		}
	});

	const { form: formData, enhance, errors, message } = form;
</script>

<!-- {JSON.stringify(data)} -->

<div class="container">
	<!-- message -->
	{#if $message}
		<div class="mb-4 rounded border border-green-200 bg-green-100 p-4 text-center">
			<p class="text-green-700">{$message}</p>
		</div>
	{/if}
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-4xl font-bold">Ingredients:</h1>

		{#if data.authenticatedUser && data.authenticatedUser.is_superuser}
			<Dialog.Root bind:open={dialogOpen}>
				<Dialog.Trigger
					class="bg-primary text-primary-foreground ring-offset-background hover:bg-primary/90 focus-visible:ring-ring inline-flex h-10 w-full items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 sm:w-auto"
				>
					Create Ingredient
				</Dialog.Trigger>
				<Dialog.Content class="sm:max-w-md">
					<Dialog.Header>
						<Dialog.Title>Create New Ingredient</Dialog.Title>
						<Dialog.Description>Add a new ingredient to the database.</Dialog.Description>
					</Dialog.Header>

					<form method="POST" action="?/create" use:enhance class="space-y-4">
						<div class="grid grid-cols-1 gap-2">
							<Field {form} name="title">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">Title *</Label>
										<!-- <Input
											{...props}
											type="text"
											bind:value={$formData.title}
											placeholder="Enter ingredient title"
										/> -->
										<input
											{...props}
											type="text"
											bind:value={$formData.title}
											placeholder="Enter ingredient title"
											class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
										/>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>
							<Field {form} name="calories">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">Calories *</Label>
										<!-- <Input
											{...props}
											type="number"
											bind:value={$formData.calories}
											placeholder="Calories per 100g"
										/> -->
										<input
											{...props}
											type="number"
											bind:value={$formData.calories}
											placeholder="Calories per 100g"
											class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
										/>
									{/snippet}
								</Control>
								<Description class="text-sm text-gray-500">Calories per 100g</Description>
								<FieldErrors />
							</Field>
						</div>

						<Dialog.Footer class="mt-6">
							<Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
								Cancel
							</Button>
							<Button type="submit">Create Ingredient</Button>
						</Dialog.Footer>
					</form>
				</Dialog.Content>
			</Dialog.Root>
		{/if}
	</div>

	{#each data.ingredients as ingredient}
		<Ingredient user={data.authenticatedUser} {ingredient} />
	{/each}
</div>

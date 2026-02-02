<script lang="ts">
	let { data } = $props();
	import DataTable from '$lib/components/ui/data-table.svelte';
	import Button, { buttonVariants } from '$lib/components/ui/button/button.svelte';
	import { enhance } from '$app/forms';
	import { createColumns } from './columns.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { superForm } from 'sveltekit-superforms';
	import { zod4 as zodClient } from 'sveltekit-superforms/adapters';
	import { fade } from 'svelte/transition';
	import { untrack } from 'svelte';
	import { DrinkSchema, DrinkUpdateSchema } from '$lib/schemas/schemas';
	import { Field, Control, Label, FieldErrors } from 'formsnap';

	let open = $state(false);

	const form = superForm(untrack(() => data.drinkCreateForm), {
		id: 'drinkCreateForm',
		validators: zodClient(DrinkSchema),
		resetForm: true,
		onUpdated: ({ form }) => {
			if (form.valid && form.message) {
				open = false;
			}
		}
	});

	const updateForm = superForm(untrack(() => data.drinkUpdateForm), {
		id: 'drinkUpdateForm',
		validators: zodClient(DrinkUpdateSchema),
		resetForm: false, // manual population
		onUpdated: ({ form }) => {
			if (form.valid && form.message) {
				console.log('Update form valid:', form.message);
			}
		}
	});

	const { form: formData, enhance: formEnhance, message } = form;
	const { message: updateMessage } = updateForm;

	$effect(() => {
		if ($message) {
			const timer = setTimeout(() => {
				$message = undefined;
			}, 3000);
			return () => clearTimeout(timer);
		}
	});

	$effect(() => {
		if ($updateMessage) {
			const timer = setTimeout(() => {
				$updateMessage = undefined;
			}, 3000);
			return () => clearTimeout(timer);
		}
	});

	const columns = createColumns(updateForm);
</script>

<div class="mx-auto max-w-7xl">
	<div class="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<h1 class="text-2xl font-bold">Drinks</h1>

		{#if $message && $message.includes('successfully')}
			<div
				out:fade
				class="rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-900/50 dark:bg-green-900/20"
			>
				<p class="text-sm text-green-800 dark:text-green-300">{$message}</p>
			</div>
		{/if}

		{#if $updateMessage && $updateMessage.includes('successfully')}
			<div
				out:fade
				class="rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-900/50 dark:bg-green-900/20"
			>
				<p class="text-sm text-green-800 dark:text-green-300">{$updateMessage}</p>
			</div>
		{/if}

		<Dialog.Root bind:open>
			<Dialog.Trigger class={buttonVariants({ variant: 'default' })}>
				Add drink
			</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[425px]">
				<Dialog.Header>
					<Dialog.Title>Add New Drink</Dialog.Title>
					<Dialog.Description>
						Add a new drink to the game. Enter the drink name below.
					</Dialog.Description>
				</Dialog.Header>
				<form method="POST" action="?/addDrink" use:formEnhance class="space-y-4 py-4">
					{#if $message && !$message.includes('successfully')}
						<div class="rounded-md border border-red-200 bg-red-50 p-3">
							<p class="text-sm text-red-600">{$message}</p>
						</div>
					{/if}

					<Field {form} name="name">
						<Control>
							{#snippet children({ props })}
								<Label>Name</Label>
								<Input {...props} bind:value={$formData.name} placeholder="Enter drink name" />
							{/snippet}
						</Control>
						<FieldErrors />
					</Field>

					<Dialog.Footer>
						<Button type="submit">Add Drink</Button>
					</Dialog.Footer>
				</form>
			</Dialog.Content>
		</Dialog.Root>
	</div>
	<DataTable
		data={data.drinks}
		{columns}
		searchColumn="name"
		searchPlaceholder="Filter drinks..."
	/>
</div>

<!-- {JSON.stringify(data.drinks)} -->

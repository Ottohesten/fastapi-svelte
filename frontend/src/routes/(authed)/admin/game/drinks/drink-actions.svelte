<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { invalidateAll } from '$app/navigation';

	import type { components } from '$lib/api/v1';

	let { drink }: { drink: components['schemas']['DrinkPublic'] } = $props();

	let editOpen = $state(false);
	let editDrinkName = $state('');
	let editError = $state('');
	let isSubmitting = $state(false);

	// Reset form when dialog opens/closes
	$effect(() => {
		if (editOpen) {
			editDrinkName = drink.name;
			editError = '';
		} else {
			editDrinkName = '';
			editError = '';
		}
	});

	// Clear error when user starts typing
	$effect(() => {
		if (editDrinkName && editError) {
			editError = '';
		}
	});
</script>

<div class="flex items-center justify-end">
	<Dialog.Root bind:open={editOpen}>
		<Dialog.Trigger>
			<Button variant="ghost" title="Edit drink" size="sm" class="p-2 hover:bg-gray-200">
				<Pencil class="" />
			</Button>
		</Dialog.Trigger>
		<Dialog.Content class="sm:max-w-[425px]">
			<Dialog.Header>
				<Dialog.Title>Edit Drink</Dialog.Title>
				<Dialog.Description>Update the drink name below.</Dialog.Description>
			</Dialog.Header>
			<form
				method="POST"
				action="?/updateDrink"
				use:enhance={() => {
					isSubmitting = true;
					editError = '';

					return async ({ result }) => {
						isSubmitting = false;
						if (result.type === 'success') {
							editOpen = false;
							editDrinkName = '';
							editError = '';
							// Refresh the data to show the updated drink
							invalidateAll();
						} else if (result.type === 'failure' && result.data) {
							editError = (result.data as any)?.error || 'An error occurred';
						}
					};
				}}
			>
				<input type="hidden" name="drink_id" value={drink.id} />
				<div class="py-4">
					{#if editError}
						<div class="rounded-md border border-red-200 bg-red-50 p-3">
							<p class="text-sm text-red-600">{editError}</p>
						</div>
					{/if}
					<div class="items-center">
						<label for="edit-name" class="">Name</label>
						<Input
							id="edit-name"
							name="name"
							bind:value={editDrinkName}
							class="mt-2"
							placeholder="Enter drink name"
							required
							disabled={isSubmitting}
						/>
					</div>
				</div>
				<Dialog.Footer>
					<Button type="submit" disabled={isSubmitting}>
						{isSubmitting ? 'Updating...' : 'Update Drink'}
					</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	<form action="?/deleteDrink" method="POST" use:enhance>
		<input type="hidden" name="drink_id" value={drink.id} />
		<Button
			variant="ghost"
			title="Delete drink"
			size="sm"
			class="p-2 text-red-600 hover:bg-red-100 hover:text-red-700"
			type="submit"
			onclick={(e) => {
				const confirmed = confirm(
					`Are you sure you want to delete drink "${drink.name}"? This action cannot be undone.`
				);
				if (!confirmed) {
					e.preventDefault();
				}
			}}
		>
			<Trash2 class="" />
		</Button>
	</form>
</div>

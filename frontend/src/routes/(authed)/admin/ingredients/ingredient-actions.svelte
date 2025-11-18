<script lang="ts">
	import Button, { buttonVariants } from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { invalidateAll } from '$app/navigation';

	import type { components } from '$lib/api/v1';

	let { ingredient }: { ingredient: components['schemas']['IngredientPublic'] } = $props();

	let editOpen = $state(false);
	let editTitle = $state('');
	let editCalories = $state(0);
	let editWeightPerPiece = $state(100);
	let editError = $state('');
	let isSubmitting = $state(false);

	// Reset form when dialog opens/closes
	$effect(() => {
		if (editOpen) {
			editTitle = ingredient.title;
			editCalories = ingredient.calories;
			editWeightPerPiece = ingredient.weight_per_piece;
			editError = '';
		} else {
			editTitle = '';
			editCalories = 0;
			editWeightPerPiece = 1;
			editError = '';
		}
	});

	// Clear error when user starts typing
	$effect(() => {
		if ((editTitle || editCalories || editWeightPerPiece) && editError) {
			editError = '';
		}
	});
</script>

<div class="flex items-center justify-end">
	<Dialog.Root bind:open={editOpen}>
		<Dialog.Trigger class={buttonVariants({ variant: 'ghost', size: 'sm', class: 'p-2' })}>
			<Pencil class="" />
		</Dialog.Trigger>
		<Dialog.Content class="sm:max-w-[425px]">
			<Dialog.Header>
				<Dialog.Title>Edit Ingredient</Dialog.Title>
				<Dialog.Description>Update the ingredient details below.</Dialog.Description>
			</Dialog.Header>
			<form
				method="POST"
				action="?/update"
				use:enhance={() => {
					isSubmitting = true;
					editError = '';

					return async ({ result }) => {
						isSubmitting = false;
						if (result.type === 'success') {
							editOpen = false;
							editTitle = '';
							editCalories = 0;
							editWeightPerPiece = 1;
							editError = '';
							invalidateAll();
						} else if (result.type === 'failure' && result.data) {
							editError = (result.data as any)?.error || 'An error occurred';
						}
					};
				}}
			>
				<input type="hidden" name="id" value={ingredient.id} />
				<div class="space-y-4 py-4">
					{#if editError}
						<div class="rounded-md border border-red-200 bg-red-50 p-3">
							<p class="text-sm text-red-600">{editError}</p>
						</div>
					{/if}
					<div class="items-center">
						<label for="edit-title" class="">Name</label>
						<Input
							id="edit-title"
							name="title"
							bind:value={editTitle}
							class="mt-2"
							placeholder="Enter ingredient name"
							required
							disabled={isSubmitting}
						/>
					</div>
					<div class="items-center">
						<label for="edit-calories" class="">Calories (per 100g)</label>
						<Input
							id="edit-calories"
							name="calories"
							type="number"
							bind:value={editCalories}
							class="mt-2"
							placeholder="Enter calories"
							required
							disabled={isSubmitting}
							min="0"
						/>
					</div>
					<div class="items-center">
						<label for="edit-weight" class="">Weight per piece (g)</label>
						<Input
							id="edit-weight"
							name="weight_per_piece"
							type="number"
							bind:value={editWeightPerPiece}
							class="mt-2"
							placeholder="Enter weight per piece"
							required
							disabled={isSubmitting}
							min="1"
						/>
					</div>
				</div>
				<Dialog.Footer>
					<Button type="submit" disabled={isSubmitting}>
						{isSubmitting ? 'Updating...' : 'Update Ingredient'}
					</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	<form action="?/delete" method="POST" use:enhance>
		<input type="hidden" name="id" value={ingredient.id} />
		<Button
			variant="ghost"
			title="Delete ingredient"
			size="sm"
			class="p-2 text-red-600 hover:bg-red-100 hover:text-red-700"
			type="submit"
			onclick={(e) => {
				const confirmed = confirm(
					`Are you sure you want to delete ingredient "${ingredient.title}"? This action cannot be undone.`
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

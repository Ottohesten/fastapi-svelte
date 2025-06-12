<script lang="ts">
	let { data } = $props();
	import DataTable from '$lib/components/ui/data-table.svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import { enhance } from '$app/forms';
	import { columns } from './columns.js';
	import { invalidateAll } from '$app/navigation';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	let open = $state(false);
	let drinkName = $state('');
	let error = $state('');
	let isSubmitting = $state(false);

	// Reset error when dialog closes or when user starts typing
	$effect(() => {
		if (!open) {
			error = '';
			drinkName = '';
		}
	});

	$effect(() => {
		if (drinkName && error) {
			error = '';
		}
	});
</script>

<div class="mx-auto max-w-7xl">
	<div class="mb-4 flex items-center justify-between">
		<h1 class="text-2xl font-bold">Drinks</h1>
		<Dialog.Root bind:open>
			<Dialog.Trigger>
				<Button>Add drink</Button>
			</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[425px]">
				<Dialog.Header>
					<Dialog.Title>Add New Drink</Dialog.Title>
					<Dialog.Description>
						Add a new drink to the game. Enter the drink name below.
					</Dialog.Description>
				</Dialog.Header>
				<form
					method="POST"
					action="?/addDrink"
					use:enhance={() => {
						isSubmitting = true;
						error = '';

						return async ({ result }) => {
							isSubmitting = false;
							if (result.type === 'success') {
								open = false;
								drinkName = '';
								error = '';
								// Refresh the data to show the new drink
								invalidateAll();
							} else if (result.type === 'failure' && result.data) {
								error = (result.data as any)?.error || 'An error occurred';
							}
						};
					}}
				>
					<div class="grid gap-4 py-4">
						{#if error}
							<div class="rounded-md border border-red-200 bg-red-50 p-3">
								<p class="text-sm text-red-600">{error}</p>
							</div>
						{/if}
						<div class="grid grid-cols-4 items-center gap-4">
							<label for="name" class="text-right">Name</label>
							<Input
								id="name"
								name="name"
								bind:value={drinkName}
								class="col-span-3"
								placeholder="Enter drink name"
								required
								disabled={isSubmitting}
							/>
						</div>
					</div>
					<Dialog.Footer>
						<Button type="submit" disabled={isSubmitting}>
							{isSubmitting ? 'Adding...' : 'Add Drink'}
						</Button>
					</Dialog.Footer>
				</form>
			</Dialog.Content>
		</Dialog.Root>
	</div>
	<DataTable data={data.drinks} {columns} />
</div>

<!-- {JSON.stringify(data.drinks)} -->

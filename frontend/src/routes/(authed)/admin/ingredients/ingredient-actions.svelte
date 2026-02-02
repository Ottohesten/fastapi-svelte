<script lang="ts">
	import Button, { buttonVariants } from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { Field, Control, Label, FieldErrors } from 'formsnap';
	import { untrack } from 'svelte';

	import type { components } from '$lib/api/v1';
	import type { SuperForm } from 'sveltekit-superforms';
	import type { Infer } from 'sveltekit-superforms';
	import type { IngredientUpdateSchema } from '$lib/schemas/schemas';

	let {
		ingredient,
		updateForm
	}: {
		ingredient: components['schemas']['IngredientPublic'];
		updateForm: SuperForm<Infer<typeof IngredientUpdateSchema>>;
	} = $props();

	const { form: formData, enhance: formEnhance, message } = untrack(() => updateForm);

	let editOpen = $state(false);

	function openEdit() {
		formData.update(($f) => ({
			...$f,
			id: ingredient.id,
			title: ingredient.title,
			calories: ingredient.calories,
			weight_per_piece: ingredient.weight_per_piece
		}));
		editOpen = true;
	}

	$effect(() => {
		if ($message && editOpen) {
			if ($message.includes('successfully')) {
				editOpen = false;
			}
		}
	});
</script>

<div class="flex items-center justify-end gap-2">
	<Dialog.Root bind:open={editOpen}>
		<Dialog.Trigger
			class={buttonVariants({ variant: 'ghost', size: 'sm', class: 'p-2' })}
			onclick={openEdit}
		>
			<Pencil class="" />
		</Dialog.Trigger>
		<Dialog.Content class="sm:max-w-[425px]">
			<Dialog.Header>
				<Dialog.Title>Edit Ingredient</Dialog.Title>
				<Dialog.Description>Update the ingredient details below.</Dialog.Description>
			</Dialog.Header>
			<form method="POST" action="?/update" use:formEnhance class="space-y-4 py-4">
				<input type="hidden" name="id" value={$formData.id} />

				{#if $message && !$message.includes('successfully')}
					<div class="rounded-md border border-red-200 bg-red-50 p-3">
						<p class="text-sm text-red-600">{$message}</p>
					</div>
				{/if}

				<Field form={updateForm} name="title">
					<Control>
						{#snippet children({ props })}
							<Label>Name</Label>
							<Input {...props} bind:value={$formData.title} placeholder="Enter ingredient name" />
						{/snippet}
					</Control>
					<FieldErrors />
				</Field>

				<Field form={updateForm} name="calories">
					<Control>
						{#snippet children({ props })}
							<Label>Calories (per 100g)</Label>
							<Input
								{...props}
								type="number"
								bind:value={$formData.calories}
								placeholder="Enter calories"
								min="0"
							/>
						{/snippet}
					</Control>
					<FieldErrors />
				</Field>

				<Field form={updateForm} name="weight_per_piece">
					<Control>
						{#snippet children({ props })}
							<Label>Weight per piece (g)</Label>
							<Input
								{...props}
								type="number"
								bind:value={$formData.weight_per_piece}
								placeholder="Enter weight per piece"
								min="1"
							/>
						{/snippet}
					</Control>
					<FieldErrors />
				</Field>

				<Dialog.Footer>
					<Button type="submit">Update Ingredient</Button>
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

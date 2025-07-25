<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	let { data } = $props();
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import InstructionsEditor from '$lib/components/InstructionsEditor.svelte';

	// const { form, errors, message, constraints, enhance } = superForm(data.form);

	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});

	// const file = fileProxy(form, 'image');

	// let selectedIngredients = $state<{ title: string; id: string }[]>([]);
	let selectedIngredientId = $state<string>('');
	let open = $state(false);
</script>

<!-- <SuperDebug data={$form} /> -->

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
	<div class="container mx-auto max-w-7xl px-4">
		<!-- Page Header -->
		<div class="mb-8">
			<h1 class="mb-2 text-3xl font-bold text-gray-900">Create New Recipe</h1>
			<p class="text-gray-600">Share your culinary creation with the world</p>
		</div>

		{#if $message}
			<div class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
				<h3 class="text-center text-lg font-medium text-green-800">{$message}</h3>
			</div>
		{/if}

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
			<!-- Main Form -->
			<div class="lg:col-span-2">
				<div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
					<form method="POST" action="" enctype="multipart/form-data" use:enhance class="space-y-6">
						<!-- Title Field -->
						<div class="space-y-2">
							<label class="text-sm font-semibold text-gray-700" for="title">
								Recipe Title <span class="text-red-500">*</span>
							</label>
							<input
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
								type="text"
								name="title"
								placeholder="Enter a delicious recipe name..."
								aria-invalid={$errors.title ? 'true' : undefined}
								bind:value={$form.title}
								{...$constraints.title}
								required
							/>
							{#if $errors.title}
								<span class="flex items-center gap-1 text-sm text-red-600">
									<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
										<path
											fill-rule="evenodd"
											d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
											clip-rule="evenodd"
										/>
									</svg>
									{$errors.title}
								</span>
							{/if}
						</div>

						<!-- Instructions Field -->
						<div class="space-y-2">
							<label class="text-sm font-semibold text-gray-700" for="instructions">
								Cooking Instructions <span class="text-red-500">*</span>
							</label>
							<div
								class="rounded-lg border border-gray-300 bg-white shadow-sm transition-colors focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20"
							>
								<InstructionsEditor bind:value={$form.instructions} />
							</div>
							<input type="hidden" name="instructions" bind:value={$form.instructions} />
							{#if $errors.instructions}
								<span class="flex items-center gap-1 text-sm text-red-600">
									<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
										<path
											fill-rule="evenodd"
											d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
											clip-rule="evenodd"
										/>
									</svg>
									{$errors.instructions}
								</span>
							{/if}
						</div>

						<!-- Add Ingredient Section -->
						<div class="space-y-2">
							<label class="text-sm font-semibold text-gray-700">Ingredients</label>
							<Dialog.Root bind:open>
								<Dialog.Trigger
									onclick={(event) => {
										event.preventDefault();
										open = true;
									}}
									class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
								>
									<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M12 6v6m0 0v6m0-6h6m-6 0H6"
										/>
									</svg>
									Add Ingredient
								</Dialog.Trigger>
								<Dialog.Content class="sm:max-w-md">
									<Dialog.Header>
										<Dialog.Title class="text-lg font-semibold text-gray-900"
											>Add Ingredient</Dialog.Title
										>
										<Dialog.Description class="text-sm text-gray-600">
											Select an ingredient to add to your recipe.
										</Dialog.Description>
									</Dialog.Header>
									<div class="space-y-4">
										<div>
											<label class="mb-2 block text-sm font-medium text-gray-700"
												>Choose Ingredient</label
											>
											<select
												class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
												bind:value={selectedIngredientId}
											>
												<option value="">Select an ingredient...</option>
												{#each data.ingredients as ingredient}
													<option value={ingredient.id}>{ingredient.title}</option>
												{/each}
											</select>
										</div>
									</div>
									<Dialog.Footer class="flex gap-3">
										<button
											type="button"
											class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
											onclick={() => {
												open = false;
											}}
										>
											Cancel
										</button>
										<button
											type="button"
											class="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-300"
											disabled={!selectedIngredientId}
											onclick={(event) => {
												event.preventDefault();
												const ingredient = data.ingredients.find(
													(i) => i.id === selectedIngredientId
												);
												if (ingredient) {
													$form.ingredients = $form.ingredients.concat(ingredient);
													data.ingredients = data.ingredients.filter(
														(i) => i.id !== selectedIngredientId
													);
													selectedIngredientId = '';
													open = false;
												} else {
													alert('Ingredient not found');
												}
											}}
										>
											Add Ingredient
										</button>
									</Dialog.Footer>
								</Dialog.Content>
							</Dialog.Root>
						</div>

						<!-- Submit Button -->
						<div class="border-t border-gray-200 pt-4">
							<button
								class="w-full rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-3 text-base font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-blue-800 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
								type="submit"
								onclick={() => {
									console.log($form.ingredients);
								}}
							>
								Create Recipe
							</button>
						</div>
					</form>
				</div>
			</div>

			<!-- Ingredients Sidebar -->
			<div class="lg:col-span-1">
				<div class="sticky top-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
					<div class="mb-4 flex items-center gap-2">
						<svg
							class="h-5 w-5 text-green-600"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<h2 class="text-lg font-semibold text-gray-900">Recipe Ingredients</h2>
					</div>

					{#if $form.ingredients.length === 0}
						<div class="py-8 text-center">
							<div
								class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100"
							>
								<svg
									class="h-8 w-8 text-gray-400"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
									/>
								</svg>
							</div>
							<p class="text-sm text-gray-500">No ingredients added yet</p>
							<p class="mt-1 text-xs text-gray-400">Click "Add Ingredient" to get started</p>
						</div>
					{:else}
						<div class="space-y-3">
							{#each $form.ingredients as ingredient, index}
								<div
									class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
								>
									<div class="flex items-center gap-3">
										<span
											class="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-600"
										>
											{index + 1}
										</span>
										<span class="text-sm font-medium text-gray-900">{ingredient.title}</span>
									</div>
									<button
										type="button"
										onclick={() => {
											$form.ingredients = $form.ingredients.filter((i) => i.id !== ingredient.id);
											data.ingredients = data.ingredients.concat(ingredient);
										}}
										class="rounded-lg p-1.5 text-red-500 transition-colors hover:bg-red-50 hover:text-red-700"
										title="Remove ingredient"
									>
										<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
										</svg>
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	/* Custom styles for enhanced visual appeal */
	:global(.tiptap-container .tiptap) {
		min-height: 200px;
		padding: 1rem;
		border-radius: 0.5rem;
		background: white;
	}

	:global(.instructions-editor .control-group) {
		margin-bottom: 0;
		padding: 0.75rem;
		background: #f8fafc;
		border-top-left-radius: 0.5rem;
		border-top-right-radius: 0.5rem;
		border-bottom: 1px solid #e2e8f0;
	}
</style>

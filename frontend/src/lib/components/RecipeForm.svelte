<script lang="ts">
	import { superForm } from 'sveltekit-superforms';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import InstructionsEditor from '$lib/components/InstructionsEditor.svelte';

	interface Props {
		data: any;
		pageTitle: string;
		pageDescription: string;
		submitButtonText: string;
		submitButtonColor?: 'blue' | 'emerald';
		onSubmit?: () => void;
	}

	let {
		data,
		pageTitle,
		pageDescription,
		submitButtonText,
		submitButtonColor = 'blue',
		onSubmit
	}: Props = $props();

	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});

	// Ingredient dialog state
	let selectedIngredientId = $state<string>('');
	let ingredientAmount = $state<number>(1.0);
	let ingredientUnit = $state<string>('g');
	let open = $state(false);

	// Color variations for submit button
	const colorClasses = {
		blue: 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:ring-blue-500',
		emerald:
			'bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 focus:ring-emerald-500'
	};
</script>

<div
	class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 dark:from-gray-950 dark:to-gray-900"
>
	<div class="container mx-auto max-w-7xl px-4">
		<!-- Page Header -->
		<div class="mb-8">
			<h1 class="mb-2 text-3xl font-bold text-gray-900 dark:text-gray-100">{pageTitle}</h1>
			<p class="text-gray-600 dark:text-gray-300">{pageDescription}</p>
		</div>

		{#if $message}
			<div
				class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900/50 dark:bg-green-900/20"
			>
				<h3 class="text-center text-lg font-medium text-green-800 dark:text-green-300">
					{$message}
				</h3>
			</div>
		{/if}

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
			<!-- Main Form -->
			<div class="lg:col-span-2">
				<div class="surface-2 rounded-xl p-6">
					<form method="POST" action="" enctype="multipart/form-data" use:enhance class="space-y-6">
						<!-- Title Field -->
						<div class="space-y-2">
							<label class="text-sm font-semibold text-gray-700 dark:text-gray-200" for="title">
								Recipe Title <span class="text-red-500">*</span>
							</label>
							<input
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
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

						<!-- Servings -->
						<div class="space-y-2">
							<label class="text-sm font-semibold text-gray-700 dark:text-gray-200" for="servings">
								Servings <span class="text-red-500">*</span>
							</label>
							<input
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
								type="number"
								name="servings"
								min="1"
								placeholder="Enter number of servings"
								aria-invalid={$errors.servings ? 'true' : undefined}
								bind:value={$form.servings}
								{...$constraints.servings}
								required
							/>
							{#if $errors.servings}
								<span class="flex items-center gap-1 text-sm text-red-600">
									<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
										<path
											fill-rule="evenodd"
											d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
											clip-rule="evenodd"
										/>
									</svg>
									{$errors.servings}
								</span>
							{/if}
						</div>

						<!-- Instructions Field -->
						<div class="space-y-2">
							<label
								class="text-sm font-semibold text-gray-700 dark:text-gray-200"
								for="instructions"
							>
								Cooking Instructions <span class="text-red-500">*</span>
							</label>
							<div
								class="rounded-lg border border-gray-300 bg-white shadow-sm transition-colors focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:focus-within:border-blue-400 dark:focus-within:ring-blue-400/20"
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
							<label
								class="text-sm font-semibold text-gray-700 dark:text-gray-200"
								for="add-ingredient-trigger"
							>
								Ingredients
							</label>
							<Dialog.Root bind:open>
								<Dialog.Trigger
									id="add-ingredient-trigger"
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
										<Dialog.Title class="text-lg font-semibold text-gray-900 dark:text-gray-100">
											Add Ingredient
										</Dialog.Title>
										<Dialog.Description class="text-sm text-gray-600 dark:text-gray-300">
											Select an ingredient to add to your recipe.
										</Dialog.Description>
									</Dialog.Header>
									<div class="space-y-4">
										<div>
											<label
												class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-200"
												for="ingredient-select"
											>
												Choose Ingredient
											</label>
											<select
												id="ingredient-select"
												class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
												bind:value={selectedIngredientId}
											>
												<option value="">Select an ingredient...</option>
												{#each data.ingredients as ingredient}
													<option value={ingredient.id}>{ingredient.title}</option>
												{/each}
											</select>
										</div>

										<div class="grid grid-cols-2 gap-3">
											<div>
												<label
													for="ingredient-amount"
													class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-200"
												>
													Amount
												</label>
												<input
													id="ingredient-amount"
													type="number"
													min="0.1"
													step="0.1"
													class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
													bind:value={ingredientAmount}
													placeholder="1"
												/>
											</div>
											<div>
												<label
													for="ingredient-unit"
													class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-200"
												>
													Unit
												</label>
												<select
													id="ingredient-unit"
													class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
													bind:value={ingredientUnit}
												>
													<option value="g">grams (g)</option>
													<option value="kg">kilograms (kg)</option>
													<option value="ml">milliliters (ml)</option>
													<option value="L">liters (L)</option>
													<option value="pcs">pieces (pcs)</option>
												</select>
											</div>
										</div>
									</div>
									<Dialog.Footer class="flex gap-3">
										<button
											type="button"
											class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
											onclick={() => {
												// Reset form when canceling
												selectedIngredientId = '';
												ingredientAmount = 1.0;
												ingredientUnit = 'g';
												open = false;
											}}
										>
											Cancel
										</button>
										<button
											type="button"
											class="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-300"
											disabled={!selectedIngredientId ||
												!ingredientAmount ||
												ingredientAmount < 0.1}
											onclick={(event) => {
												event.preventDefault();
												const ingredient = data.ingredients.find(
													(i: any) => i.id === selectedIngredientId
												);
												if (ingredient) {
													// Create the ingredient link object that matches your schema
													const ingredientLink = {
														id: ingredient.id,
														title: ingredient.title,
														calories: ingredient.calories,
														amount: ingredientAmount,
														unit: ingredientUnit as 'g' | 'kg' | 'ml' | 'L' | 'pcs'
													};
													$form.ingredients = $form.ingredients.concat({
														id: ingredientLink.id,
														title: ingredientLink.title, // Include title for display
														amount: ingredientLink.amount,
														unit: ingredientLink.unit
													});
													data.ingredients = data.ingredients.filter(
														(i: any) => i.id !== selectedIngredientId
													);
													// Reset form
													selectedIngredientId = '';
													ingredientAmount = 1.0;
													ingredientUnit = 'g';
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
						<div class="border-t border-gray-200 pt-4 dark:border-gray-800">
							<button
								class="w-full rounded-lg {colorClasses[
									submitButtonColor
								]} px-6 py-3 text-base font-semibold text-white shadow-lg transition-all hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-gray-900"
								type="submit"
								onclick={() => {
									onSubmit?.();
								}}
							>
								{submitButtonText}
							</button>
						</div>
					</form>
				</div>
			</div>

			<!-- Ingredients Sidebar -->
			<div class="lg:col-span-1">
				<div class="surface-2 sticky top-8 rounded-xl p-6">
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
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
							Recipe Ingredients
						</h2>
					</div>

					{#if $form.ingredients.length === 0}
						<div class="py-8 text-center">
							<div
								class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800"
							>
								<svg
									class="h-8 w-8 text-gray-400 dark:text-gray-500"
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
							<p class="text-sm text-gray-500 dark:text-gray-400">No ingredients added yet</p>
							<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
								Click "Add Ingredient" to get started
							</p>
						</div>
					{:else}
						<div class="space-y-3">
							{#each $form.ingredients as ingredient, index}
								<div
									class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900/40 dark:hover:bg-gray-900/60"
								>
									<div class="flex items-center gap-3">
										<span
											class="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-600 dark:bg-blue-900/30 dark:text-blue-300"
										>
											{index + 1}
										</span>
										<div class="flex flex-col">
											<span class="text-sm font-medium text-gray-900 dark:text-gray-100">
												{ingredient.title || 'Unknown Ingredient'}
											</span>
											<span class="text-xs text-gray-500 dark:text-gray-400">
												{ingredient.amount || 0}
												{ingredient.unit || 'units'}
											</span>
										</div>
									</div>
									<button
										type="button"
										aria-label="Remove ingredient"
										onclick={() => {
											$form.ingredients = $form.ingredients.filter(
												(i: any) => i.id !== ingredient.id
											);
											// Return the ingredient to the available list if it's not already there
											const isAlreadyAvailable = data.ingredients.some(
												(ing: any) => ing.id === ingredient.id
											);
											if (!isAlreadyAvailable) {
												// Reconstruct the ingredient object for the available list
												const originalIngredient = {
													id: ingredient.id,
													title: ingredient.title || 'Unknown Ingredient',
													calories: 0 // Default calories since we don't store it in form
												};
												data.ingredients = data.ingredients.concat(originalIngredient);
											}
										}}
										class="rounded-lg p-1.5 text-red-500 transition-colors hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-900/20"
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

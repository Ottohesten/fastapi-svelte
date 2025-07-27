<script lang="ts">
	import type { components } from '$lib/api/v1';

	type Props = {
		data: {
			recipe: components['schemas']['RecipePublic'];
			authenticatedUser?: components['schemas']['UserPublic'];
			is_owner: boolean;
		};
	};

	let { data }: Props = $props();

	// State for ingredient checking (shopping list functionality)
	let checkedIngredients = $state<Set<string>>(new Set());

	// Simple step count - just count <li> elements in instructions
	const stepCount = $derived.by(() => {
		if (!data.recipe.instructions) return 0;

		// Count <li> elements as individual steps
		const liMatches = data.recipe.instructions.match(/<li[^>]*>/gi);

		return liMatches ? liMatches.length : 0;
	});

	// Toggle ingredient as checked/unchecked
	function toggleIngredient(ingredientId: string) {
		if (checkedIngredients.has(ingredientId)) {
			checkedIngredients.delete(ingredientId);
		} else {
			checkedIngredients.add(ingredientId);
		}
		checkedIngredients = new Set(checkedIngredients); // Trigger reactivity
	}
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
	<div class="container mx-auto max-w-6xl px-4 py-8">
		<!-- Header Section -->
		<div class="mb-8">
			<div class="mb-4 flex items-center gap-4">
				<a
					href="/recipes"
					class="flex items-center gap-2 text-blue-600 transition-colors hover:text-blue-800"
				>
					<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						/>
					</svg>
					Back to Recipes
				</a>
				{#if data.is_owner}
					<a
						href="/recipes/{data.recipe.id}/update"
						class="ml-auto rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
					>
						Edit Recipe
					</a>
				{/if}
			</div>

			<h1 class="mb-4 text-4xl font-bold text-gray-900">{data.recipe.title}</h1>

			<div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
						/>
					</svg>
					<span>By {data.recipe.owner.full_name}</span>
				</div>
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
						/>
					</svg>
					<span>{data.recipe.servings} servings</span>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
			<!-- Main Content -->
			<div class="lg:col-span-2">
				<!-- Recipe Stats -->
				<div
					class="mb-8 grid grid-cols-2 gap-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-4"
				>
					<div class="text-center">
						<div class="mb-2 flex items-center justify-center">
							<svg
								class="h-6 w-6 text-orange-600"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
								/>
							</svg>
						</div>
						<div class="text-2xl font-bold text-gray-900">{data.recipe.total_calories || 0}</div>
						<div class="text-sm text-gray-600">Total Calories</div>
					</div>
					<div class="text-center">
						<div class="mb-2 flex items-center justify-center">
							<svg
								class="h-6 w-6 text-green-600"
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
						</div>
						<div class="text-2xl font-bold text-gray-900">
							{data.recipe.calories_per_serving || 0}
						</div>
						<div class="text-sm text-gray-600">Per Serving</div>
					</div>
					<div class="text-center">
						<div class="mb-2 flex items-center justify-center">
							<svg
								class="h-6 w-6 text-blue-600"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
								/>
							</svg>
						</div>
						<div class="text-2xl font-bold text-gray-900">
							{data.recipe.ingredient_links.length}
						</div>
						<div class="text-sm text-gray-600">Ingredients</div>
					</div>
					<div class="text-center">
						<div class="mb-2 flex items-center justify-center">
							<svg
								class="h-6 w-6 text-purple-600"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
								/>
							</svg>
						</div>
						<div class="text-2xl font-bold text-gray-900">{stepCount}</div>
						<div class="text-sm text-gray-600">Steps</div>
					</div>
				</div>

				<!-- Instructions Section -->
				{#if data.recipe.instructions}
					<div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
						<div class="mb-4 flex items-center justify-between">
							<h2 class="text-xl font-bold text-gray-900">Cooking Instructions</h2>
						</div>

						<div class="prose prose-lg max-w-none">
							{@html data.recipe.instructions}
						</div>
					</div>
				{:else}
					<div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-gray-900">Cooking Instructions</h2>
						<p class="italic text-gray-500">No instructions provided.</p>
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="lg:col-span-1">
				<!-- Ingredients Section -->
				<div class="sticky top-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
					<div class="mb-4 flex items-center justify-between">
						<h2 class="text-xl font-bold text-gray-900">Ingredients</h2>
						<span class="text-sm text-gray-600">
							{checkedIngredients.size}/{data.recipe.ingredient_links.length} checked
						</span>
					</div>

					<div class="space-y-3">
						{#each data.recipe.ingredient_links as ingredient_link, index}
							<div
								class="flex cursor-pointer items-center gap-3 rounded-lg border border-gray-200 p-3 transition-all hover:bg-gray-50 {checkedIngredients.has(
									ingredient_link.ingredient.id
								)
									? 'border-green-200 bg-green-50'
									: ''}"
								role="button"
								tabindex="0"
								onclick={() => toggleIngredient(ingredient_link.ingredient.id)}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										toggleIngredient(ingredient_link.ingredient.id);
									}
								}}
							>
								<div class="flex-shrink-0">
									{#if checkedIngredients.has(ingredient_link.ingredient.id)}
										<svg class="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
											<path
												fill-rule="evenodd"
												d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
												clip-rule="evenodd"
											/>
										</svg>
									{:else}
										<div class="h-5 w-5 rounded-full border-2 border-gray-300"></div>
									{/if}
								</div>
								<div
									class="flex-1 {checkedIngredients.has(ingredient_link.ingredient.id)
										? 'text-gray-500 line-through'
										: ''}"
								>
									<div class="font-medium text-gray-900">{ingredient_link.ingredient.title}</div>
									<div class="text-sm text-gray-600">
										{ingredient_link.amount}
										{ingredient_link.unit}
									</div>
								</div>
							</div>
						{/each}
					</div>

					{#if data.recipe.ingredient_links.length === 0}
						<div class="py-8 text-center">
							<p class="text-gray-500">No ingredients listed</p>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

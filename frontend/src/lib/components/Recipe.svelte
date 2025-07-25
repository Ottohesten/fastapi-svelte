<script lang="ts">
	// let stuff = $props();
	// let { user, recipe } = $props();
	import { enhance } from '$app/forms';

	import type { components } from '$lib/api/v1';

	type Props = {
		recipe: components['schemas']['RecipePublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};

	let { recipe, authenticatedUser }: Props = $props();
</script>

<div
	class="group relative overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all duration-300 hover:border-gray-300 hover:shadow-lg"
>
	<a href="/recipes/{recipe.id}" class="block">
		<div class="p-6">
			<!-- Recipe Header -->
			<div class="mb-4">
				<h3
					class="line-clamp-2 text-xl font-bold text-gray-900 transition-colors duration-300 group-hover:text-blue-600"
				>
					{recipe.title}
				</h3>
				<div class="mt-2 flex items-center gap-2 text-sm text-gray-600">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
						/>
					</svg>
					<span class="font-medium">By {recipe.owner.full_name}</span>
				</div>
			</div>

			<!-- Ingredients Section -->
			<div class="mb-4">
				<div class="mb-3 flex items-center gap-2">
					<svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<p class="text-sm font-semibold text-gray-700">
						Ingredients ({recipe.ingredients.length})
					</p>
				</div>
				{#if recipe.ingredients.length > 0}
					<div class="flex flex-wrap gap-2">
						{#each recipe.ingredients.slice(0, 6) as ingredient}
							<span
								class="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700"
							>
								{ingredient.title}
							</span>
						{/each}
						{#if recipe.ingredients.length > 6}
							<span
								class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600"
							>
								+{recipe.ingredients.length - 6} more
							</span>
						{/if}
					</div>
				{:else}
					<p class="text-sm italic text-gray-500">No ingredients listed</p>
				{/if}
			</div>

			<!-- Instructions Preview -->
			<div class="mb-4">
				<div class="mb-2 flex items-center gap-2">
					<svg class="h-4 w-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
					<p class="text-sm font-semibold text-gray-700">Instructions</p>
				</div>
				<div class="prose prose-sm max-w-none">
					<div
						class="line-clamp-3 text-sm text-gray-600 [&>*]:text-sm [&>h1]:text-base [&>h2]:text-sm [&>h3]:text-sm"
					>
						{@html recipe.instructions}
					</div>
				</div>
			</div>

			<!-- Read More Indicator -->
			<div class="flex items-center justify-between">
				<div
					class="flex items-center text-sm font-medium text-blue-600 transition-colors group-hover:text-blue-700"
				>
					<span>Read full recipe</span>
					<svg
						class="ml-1 h-4 w-4 transform transition-transform group-hover:translate-x-1"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 5l7 7-7 7"
						/>
					</svg>
				</div>
			</div>
		</div>
	</a>

	<!-- Action Buttons (Edit/Delete) -->
	{#if (authenticatedUser && authenticatedUser.id === recipe.owner.id) || (authenticatedUser && authenticatedUser.is_superuser)}
		<div class="border-t border-gray-100 bg-gray-50 px-6 py-3">
			<div class="flex items-center justify-between">
				<span class="text-xs font-medium text-gray-500">Recipe Actions</span>
				<div class="flex items-center gap-2">
					<a
						href="/recipes/{recipe.id}/update"
						class="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition-colors hover:border-blue-300 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
					>
						<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
							/>
						</svg>
						Edit
					</a>
					<form action="/recipes?/delete" method="POST" use:enhance class="inline">
						<input type="hidden" name="recipe_id" value={recipe.id} />
						<button
							type="submit"
							class="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:border-red-300 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
							onclick={(e) => {
								if (
									!confirm(
										'Are you sure you want to delete this recipe? This action cannot be undone.'
									)
								) {
									e.preventDefault();
								}
							}}
						>
							<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
								/>
							</svg>
							Delete
						</button>
					</form>
				</div>
			</div>
		</div>
	{/if}
</div>

<script lang="ts">
	// let stuff = $props();
	// let { user, recipe } = $props();
	import { enhance } from '$app/forms';

	import type { components } from '$lib/api/v1';

	type Props = {
		recipe: components['schemas']['RecipePublic'];
		user?: components['schemas']['UserPublic'];
	};

	let { recipe, user }: Props = $props();
</script>

<div class="my-4 rounded-md bg-gray-100 p-4 dark:bg-gray-800">
	<a href="/recipes/{recipe.id}">
		<div class="test">
			<h3 class="font-bold">{recipe.title}</h3>
			<div>
				<p>Ingredients:</p>
				<ul>
					{#each recipe.ingredients as ingredient}
						<li>{ingredient.title}</li>
					{/each}
				</ul>
			</div>
			<div>
				<p class="font-medium">Instructions</p>
				<p>{recipe.instructions}</p>
			</div>
			<div class="mt-4 flex flex-col justify-between lg:flex-row">
				<div>
					<p>By: {recipe.owner.full_name}</p>
				</div>
			</div>
		</div>
	</a>
	{#if (user && user.id === recipe.owner.id) || (user && user.is_superuser)}
		<div class="mt-2 flex space-x-4">
			<a
				href="/recipes/{recipe.id}/update"
				class="rounded-md bg-gray-600 px-4 py-2 font-medium text-gray-300 hover:bg-gray-900 hover:text-white"
				>Edit</a
			>
			<!-- delete -->
			<form action="/recipes?/delete" method="POST" use:enhance>
				<input type="hidden" name="recipe_id" value={recipe.id} />
				<button
					class="rounded-md bg-red-600 px-4 py-2 font-medium text-gray-300 hover:bg-red-900 hover:text-white"
					type="submit"
				>
					Delete
				</button>
			</form>
		</div>
	{/if}
</div>

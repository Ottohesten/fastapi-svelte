<script lang="ts">
  import Recipe from "$lib/components/Recipe.svelte";
  import { Input } from "$lib/components/ui/input";
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();
  let searchQuery = $state("");

  let filteredRecipes = $derived.by(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return data.recipes;

    const ingredientTerms = query
      .split(",")
      .map((term) => term.trim())
      .filter((term) => term.length > 0);

    const isIngredientListSearch = query.includes(",");

    return data.recipes.filter((recipe) => {
      const ingredientTitles = recipe.ingredient_links.map((ingredientLink) =>
        ingredientLink.ingredient.title.toLowerCase()
      );

      if (isIngredientListSearch) {
        return ingredientTerms.every((term) =>
          ingredientTitles.some((ingredientTitle) => ingredientTitle.includes(term))
        );
      }

      const titleMatch = recipe.title.toLowerCase().includes(query);
      const ownerMatch = (recipe.owner.full_name ?? "").toLowerCase().includes(query);
      const ingredientMatch = ingredientTitles.some((ingredientTitle) =>
        ingredientTitle.includes(query)
      );

      return titleMatch || ownerMatch || ingredientMatch;
    });
  });
</script>

<!-- {console.log(form)} -->
<!-- {console.log(data)} -->
<!-- {JSON.stringify(data.authenticatedUser)} -->

<div class="container mx-auto px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
  <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <h1 class="mb-4 text-2xl font-bold sm:mb-0 sm:text-3xl lg:text-4xl">Recipes</h1>
    {#if data.authenticatedUser && data.scopes?.includes("recipes:create")}
      <a
        href="/recipes/create"
        class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none sm:px-6 sm:py-3 sm:text-base"
      >
        <svg
          class="mr-2 h-4 w-4 sm:h-5 sm:w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
        Create Recipe
      </a>
    {/if}
  </div>

  <div class="mb-6">
    <Input
      type="search"
      bind:value={searchQuery}
      placeholder="Search by title/owner, or ingredients: olive oil, salmon, rice"
      class="w-full sm:max-w-xl"
      aria-label="Search recipes"
    />
    <p class="mt-2 text-sm text-gray-600">
      Showing {filteredRecipes.length} of {data.recipes.length} recipes
    </p>
  </div>

  <div class="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 xl:grid-cols-3">
    {#each filteredRecipes as recipe}
      <Recipe
        {recipe}
        authenticatedUser={data.authenticatedUser
          ? { ...data.authenticatedUser, scopes: data.authenticatedUser.scopes ?? [] }
          : undefined}
      />
    {/each}
  </div>

  {#if filteredRecipes.length === 0}
    <div class="mt-8 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
      <p class="text-sm text-gray-600">No recipes match your search.</p>
    </div>
  {/if}
</div>

<!-- <form action="/recipes?/create" method="POST">
	<button
		type="submit"
		class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
	>
		submit
	</button>
</form> -->

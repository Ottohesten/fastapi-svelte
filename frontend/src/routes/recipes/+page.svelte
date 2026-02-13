<script lang="ts">
  import Recipe from "$lib/components/Recipe.svelte";
  let { data } = $props();
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

  <div class="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 xl:grid-cols-3">
    {#each data.recipes as recipe}
      <Recipe {recipe} authenticatedUser={data.authenticatedUser ?? undefined} />
    {/each}
  </div>
</div>

<!-- <form action="/recipes?/create" method="POST">
	<button
		type="submit"
		class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
	>
		submit
	</button>
</form> -->

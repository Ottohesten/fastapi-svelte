<script lang="ts">
  import type { RecipePublic, UserMePublic } from "$lib/client";
  import RecipeIngredientsChecklist from "$lib/components/RecipeIngredientsChecklist.svelte";
  import RecipeNutritionSheet from "$lib/components/RecipeNutritionSheet.svelte";

  type Props = {
    data: {
      recipe: RecipePublic;
      authenticatedUser?: UserMePublic;
      is_owner: boolean;
    };
  };

  let { data }: Props = $props();
  const subRecipeLinks = $derived(data.recipe.sub_recipe_links ?? []);
  const totalIngredients = $derived(data.recipe.total_ingredients);

  // Simple step count - just count <li> elements in instructions
  const stepCount = $derived.by(() => {
    if (!data.recipe.instructions) return 0;

    // Count <li> elements as individual steps
    const liMatches = data.recipe.instructions.match(/<li[^>]*>/gi);

    return liMatches ? liMatches.length : 0;
  });
</script>

<div
  class="min-h-screen bg-linear-to-br from-slate-50 to-blue-50 py-8 dark:from-gray-950 dark:to-gray-900"
>
  <div class="container mx-auto max-w-7xl px-4">
    <!-- Header Section -->
    <div class="mb-8">
      <div class="mb-4 flex items-center gap-4">
        <a
          href="/recipes"
          class="flex items-center gap-2 text-blue-600 transition-colors hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
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
        <div class="ml-auto flex items-center gap-2">
          <RecipeNutritionSheet recipe={data.recipe} />
          {#if data.is_owner}
            <a
              href="/recipes/{data.recipe.id}/update"
              class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
            >
              Edit Recipe
            </a>
          {/if}
        </div>
      </div>

      <h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-gray-100">{data.recipe.title}</h1>

      <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
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

    <!-- Recipe Image -->
    <div
      class="mb-8 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
    >
      <div class="relative aspect-video w-full bg-gray-100 sm:aspect-21/9 dark:bg-gray-800">
        {#if data.recipe.image}
          <img
            src={data.recipe.image}
            alt={data.recipe.title}
            class="absolute inset-0 h-full w-full object-cover"
          />
        {:else}
          <div class="flex h-full items-center justify-center text-gray-400 dark:text-gray-500">
            <svg class="h-24 w-24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        {/if}
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <!-- Main Content -->
      <div class="lg:col-span-2">
        <!-- Recipe Stats -->
        <div
          class="mb-8 grid grid-cols-2 gap-6 rounded-xl border border-gray-300 bg-white p-6 shadow-sm md:grid-cols-5 dark:border-gray-800 dark:bg-gray-900/40"
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
            <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {data.recipe.total_calories || 0}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Total Calories</div>
            <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {data.recipe.calories_per_100g || 0} cal/100g
            </div>
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
            <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {data.recipe.calories_per_serving || 0}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Per Serving</div>
          </div>
          <div class="text-center">
            <div class="mb-2 flex items-center justify-center">
              <svg
                class="h-6 w-6 text-amber-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l3-3m-3 3l-3-3"
                />
              </svg>
            </div>
            <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {data.recipe.calculated_weight || 0}g
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Total Weight</div>
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
            <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {totalIngredients.length}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Ingredients</div>
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
            <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{stepCount}</div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Steps</div>
          </div>
        </div>

        <!-- Instructions Section -->
        {#if data.recipe.instructions}
          <div
            class="rounded-xl border border-gray-300 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
          >
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">
                Cooking Instructions
              </h2>
            </div>

            <div class="prose prose-lg dark:prose-invert recipe-instructions max-w-none">
              {@html data.recipe.instructions}
            </div>
          </div>
        {:else}
          <div
            class="rounded-xl border border-gray-300 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
          >
            <h2 class="mb-4 text-xl font-bold text-gray-900 dark:text-gray-100">
              Cooking Instructions
            </h2>
            <p class="text-gray-500 italic dark:text-gray-400">No instructions provided.</p>
          </div>
        {/if}
      </div>

      <!-- Sidebar -->
      <div class="lg:sticky lg:top-8 lg:col-span-1 lg:self-start">
        <RecipeIngredientsChecklist ingredients={data.recipe.total_ingredients} />

        <div
          class="mt-4 rounded-xl border border-gray-300 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
        >
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Sub-Recipes</h2>
            <span class="text-sm text-gray-600 dark:text-gray-300">
              {subRecipeLinks.length}
            </span>
          </div>

          {#if subRecipeLinks.length === 0}
            <p class="text-sm text-gray-500 dark:text-gray-400">No sub-recipes linked</p>
          {:else}
            <div class="space-y-2">
              {#each subRecipeLinks as subRecipeLink}
                <div
                  class="rounded-lg border border-gray-300 p-3 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/60"
                >
                  <a
                    href="/recipes/{subRecipeLink.sub_recipe.id}"
                    class="text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    {subRecipeLink.sub_recipe.title}
                  </a>
                  <div class="mt-1 text-xs text-gray-600 dark:text-gray-400">
                    Scale x{subRecipeLink.scale_factor} • {subRecipeLink.scaled_servings} servings
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>

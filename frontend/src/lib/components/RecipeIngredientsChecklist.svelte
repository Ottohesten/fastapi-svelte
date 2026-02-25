<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import type { RecipeIngredientSourcePublic, RecipeIngredientTotalPublic } from "$lib/client";

  type Props = {
    ingredients: RecipeIngredientTotalPublic[];
  };

  let { ingredients }: Props = $props();

  let checkedIngredients = $state<Set<string>>(new Set());
  const ingredientCardBaseClass =
    "flex cursor-pointer items-start gap-2.5 rounded-lg border border-gray-300 p-2.5 transition-all hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/60";
  const ingredientCardCheckedClass =
    "border-green-200 bg-green-50 dark:border-green-900/50 dark:bg-green-900/20";
  const sourceBadgeBaseClass =
    "inline-flex max-w-full items-center rounded-full border px-1.5 py-0.5 text-[11px]";
  const sourceBadgeMainClass =
    "border-blue-300 bg-blue-100 text-blue-900 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-200";
  const sourceBadgeSubRecipeClass =
    "border-gray-300 bg-gray-100 text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300";

  function ingredientKey(ingredient: { ingredient_id: string; unit: string }): string {
    return `${ingredient.ingredient_id}:${ingredient.unit}`;
  }

  function ingredientCardClass(isChecked: boolean): string {
    return isChecked
      ? `${ingredientCardBaseClass} ${ingredientCardCheckedClass}`
      : ingredientCardBaseClass;
  }

  function sourceBadgeClass(source: RecipeIngredientSourcePublic): string {
    return source.is_main_recipe
      ? `${sourceBadgeBaseClass} ${sourceBadgeMainClass}`
      : `${sourceBadgeBaseClass} ${sourceBadgeSubRecipeClass}`;
  }

  function toggleIngredient(ingredient: { ingredient_id: string; unit: string }) {
    const key = ingredientKey(ingredient);
    if (checkedIngredients.has(key)) {
      checkedIngredients.delete(key);
    } else {
      checkedIngredients.add(key);
    }
    checkedIngredients = new Set(checkedIngredients);
  }

  function formatAmount(value: number): string {
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2).replace(/\.?0+$/, "");
  }
</script>

<div
  class="rounded-xl border border-gray-300 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
>
  <div class="mb-4 flex items-center justify-between">
    <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Ingredients</h2>
    <span class="text-sm text-gray-600 dark:text-gray-300">
      {checkedIngredients.size}/{ingredients.length} checked
    </span>
  </div>
  <p class="mb-4 text-xs text-gray-600 dark:text-gray-400">
    Aggregated from this recipe and all linked sub-recipes. Source badges show where each amount
    comes from.
  </p>

  {#if ingredients.length === 0}
    <div class="py-8 text-center">
      <p class="text-gray-500 dark:text-gray-400">No ingredients listed</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each ingredients as ingredient (ingredientKey(ingredient))}
        {@const isChecked = checkedIngredients.has(ingredientKey(ingredient))}
        {@const hasSources = ingredient.sources.length > 0}
        <div
          class={ingredientCardClass(isChecked)}
          role="button"
          tabindex="0"
          onclick={() => toggleIngredient(ingredient)}
          onkeydown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              toggleIngredient(ingredient);
            }
          }}
        >
          <div class="shrink-0">
            {#if isChecked}
              <svg class="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clip-rule="evenodd"
                />
              </svg>
            {:else}
              <div class="h-4 w-4 rounded-full border-2 border-gray-300 dark:border-gray-600"></div>
            {/if}
          </div>
          <div
            class="grid min-w-0 flex-1 grid-cols-1 gap-1.5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start sm:gap-2"
          >
            <div class={isChecked ? "text-gray-500 line-through dark:text-gray-400" : ""}>
              <div
                class="truncate text-sm font-medium text-gray-900 dark:text-gray-100"
                title={ingredient.title}
              >
                {ingredient.title}
              </div>
              <span class="shrink-0 text-xs text-gray-600 dark:text-gray-400">
                {formatAmount(ingredient.amount)}
                {ingredient.unit}
              </span>
            </div>
            {#if hasSources}
              <div class="flex flex-wrap gap-1 sm:max-w-[13rem] sm:flex-col sm:items-end">
                {#each ingredient.sources as source}
                  <Badge
                    variant="outline"
                    class={sourceBadgeClass(source)}
                    title={`${source.recipe_title}: ${formatAmount(source.amount)}${source.unit}`}
                  >
                    <span class="max-w-[10rem] truncate">
                      {source.is_main_recipe ? "Main recipe" : source.recipe_title}
                    </span>
                    <span class="mx-1">•</span>
                    <span class="whitespace-nowrap">
                      {formatAmount(source.amount)}{source.unit}
                    </span>
                  </Badge>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

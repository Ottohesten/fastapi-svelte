<script lang="ts">
  import { browser } from "$app/environment";
  import { tick } from "svelte";
  import type { RecipePublic, UserMePublic } from "$lib/client";
  import RecipeIngredientsChecklist from "$lib/components/RecipeIngredientsChecklist.svelte";
  import RecipeNutritionSheet from "$lib/components/RecipeNutritionSheet.svelte";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";

  type Props = {
    data: {
      recipe: RecipePublic;
      authenticatedUser?: UserMePublic;
      is_owner: boolean;
      can_edit: boolean;
    };
  };

  let { data }: Props = $props();

  const baseServings = $derived.by(() => Math.max(data.recipe.servings ?? 1, 1));
  const recipeId = $derived.by(() => data.recipe.id);
  let servingsInput = $state("");
  $effect(() => {
    servingsInput = String(baseServings);
  });
  const desiredServings = $derived.by(() => {
    const parsed = Number(servingsInput);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : baseServings;
  });
  const scaleFactor = $derived.by(() => (baseServings > 0 ? desiredServings / baseServings : 1));

  function formatAmount(value: number): string {
    if (!Number.isFinite(value)) return "0";
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2).replace(/\.?0+$/, "");
  }

  function normalizeServingsInput() {
    const parsed = Number(servingsInput);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      servingsInput = String(baseServings);
    }
  }

  function scaleValue(value: number): number {
    return value * scaleFactor;
  }

  const scaledIngredients = $derived.by(() =>
    data.recipe.total_ingredients.map((ingredient) => ({
      ...ingredient,
      amount: scaleValue(ingredient.amount),
      grams: scaleValue(ingredient.grams),
      calories: scaleValue(ingredient.calories),
      carbohydrates: scaleValue(ingredient.carbohydrates),
      fat: scaleValue(ingredient.fat),
      protein: scaleValue(ingredient.protein),
      sources: ingredient.sources.map((source) => ({
        ...source,
        amount: scaleValue(source.amount)
      }))
    }))
  );

  const subRecipeLinks = $derived.by(() =>
    (data.recipe.sub_recipe_links ?? []).map((link) => ({
      ...link,
      scale_factor: scaleValue(link.scale_factor),
      scaled_servings: scaleValue(link.scaled_servings)
    }))
  );

  const scaledRecipe = $derived.by<RecipePublic>(() => ({
    ...data.recipe,
    servings: desiredServings,
    total_ingredients: scaledIngredients,
    total_calories: scaleValue(data.recipe.total_calories ?? 0),
    total_carbohydrates: scaleValue(data.recipe.total_carbohydrates ?? 0),
    total_fat: scaleValue(data.recipe.total_fat ?? 0),
    total_protein: scaleValue(data.recipe.total_protein ?? 0),
    calculated_weight: scaleValue(data.recipe.calculated_weight ?? 0)
  }));

  const INSTRUCTION_STORAGE_PREFIX = "recipe-instruction-checks:v1:";
  const FOLLOW_ALONG_STORAGE_PREFIX = "recipe-follow-along:v1:";
  const INSTRUCTION_TTL_MS = 12 * 60 * 60 * 1000;

  let instructionsHtml = $state("");
  let checkedSteps = $state<Set<string>>(new Set());
  let instructionStepKeys = $state<string[]>([]);
  let followAlongEnabled = $state(false);
  let instructionsContainer: HTMLDivElement | null = $state(null);

  function instructionStorageKey(id: string): string {
    return `${INSTRUCTION_STORAGE_PREFIX}${id}`;
  }

  function followAlongStorageKey(id: string): string {
    return `${FOLLOW_ALONG_STORAGE_PREFIX}${id}`;
  }

  function loadFollowAlongPreference(): boolean {
    if (!browser) return false;
    const raw = localStorage.getItem(followAlongStorageKey(recipeId));
    return raw === "1";
  }

  function setFollowAlongEnabled(next: boolean) {
    followAlongEnabled = next;
    if (!browser) return;
    localStorage.setItem(followAlongStorageKey(recipeId), next ? "1" : "0");
  }

  function persistInstructionChecks() {
    if (!browser) return;
    const payload = {
      version: 1,
      expiresAt: Date.now() + INSTRUCTION_TTL_MS,
      items: Array.from(checkedSteps)
    };
    localStorage.setItem(instructionStorageKey(recipeId), JSON.stringify(payload));
  }

  function loadInstructionChecks(): Set<string> {
    if (!browser) return new Set<string>();
    const raw = localStorage.getItem(instructionStorageKey(recipeId));
    if (!raw) return new Set<string>();

    try {
      const parsed = JSON.parse(raw) as { expiresAt?: number; items?: string[] };
      if (!parsed?.expiresAt || parsed.expiresAt <= Date.now()) {
        localStorage.removeItem(instructionStorageKey(recipeId));
        return new Set<string>();
      }
      if (!Array.isArray(parsed.items)) return new Set<string>();
      return new Set(parsed.items.filter((item) => typeof item === "string"));
    } catch {
      localStorage.removeItem(instructionStorageKey(recipeId));
      return new Set<string>();
    }
  }

  function buildCheckableInstructions(html: string) {
    if (!browser) return { html, keys: [] as string[] };

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const keys: string[] = [];

    const lists = Array.from(doc.querySelectorAll("ol, ul"));
    lists.forEach((list, listIndex) => {
      const items = Array.from(list.querySelectorAll(":scope > li"));
      items.forEach((li, itemIndex) => {
        const stepIndex = itemIndex + 1;
        const stepKey = `list-${listIndex + 1}-step-${stepIndex}`;
        keys.push(stepKey);

        const checkbox = doc.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "recipe-step-checkbox";
        checkbox.setAttribute("data-step-key", stepKey);
        checkbox.setAttribute("aria-label", `Mark step ${stepIndex} complete`);
        const indicator = doc.createElement("span");
        indicator.className = "recipe-step-indicator";
        if (list.tagName.toLowerCase() === "ol") {
          indicator.textContent = String(stepIndex);
        }

        const wrapper = doc.createElement("div");
        wrapper.className = "recipe-step-text";
        while (li.firstChild) {
          wrapper.appendChild(li.firstChild);
        }

        li.setAttribute("data-step-key", stepKey);
        li.setAttribute("data-step-checked", "false");
        li.appendChild(checkbox);
        li.appendChild(indicator);
        li.appendChild(wrapper);
      });
    });

    return { html: doc.body.innerHTML, keys };
  }

  function handleInstructionChange(event: Event) {
    if (!followAlongEnabled) return;
    const target = event.target as HTMLInputElement | null;
    if (!target || target.getAttribute("data-step-key") == null) return;
    const key = target.getAttribute("data-step-key") ?? "";
    if (!key) return;

    if (target.checked) {
      checkedSteps.add(key);
    } else {
      checkedSteps.delete(key);
    }
    checkedSteps = new Set(checkedSteps);
    applyInstructionChecks();
    persistInstructionChecks();
  }

  function handleInstructionClick(event: MouseEvent) {
    if (!followAlongEnabled) return;
    const target = event.target as HTMLElement | null;
    if (!target) return;
    if (target.closest("a")) return;
    if (target instanceof HTMLInputElement && target.type === "checkbox") return;

    const li = target.closest("li[data-step-key]") as HTMLLIElement | null;
    if (!li) return;
    const checkbox = li.querySelector<HTMLInputElement>("input.recipe-step-checkbox");
    if (!checkbox) return;
    checkbox.checked = !checkbox.checked;
    checkbox.dispatchEvent(new Event("change", { bubbles: true }));
  }

  $effect(() => {
    if (!browser) return;
    checkedSteps = loadInstructionChecks();
  });

  $effect(() => {
    if (!browser) return;
    followAlongEnabled = loadFollowAlongPreference();
  });

  $effect(() => {
    if (!browser) {
      instructionsHtml = data.recipe.instructions ?? "";
      instructionStepKeys = [];
      return;
    }
    if (!followAlongEnabled) {
      instructionsHtml = data.recipe.instructions ?? "";
      instructionStepKeys = [];
      return;
    }
    const { html, keys } = buildCheckableInstructions(data.recipe.instructions ?? "");
    instructionsHtml = html;
    instructionStepKeys = keys;
  });

  $effect(() => {
    if (!browser || instructionStepKeys.length === 0) return;
    const validKeys = new Set(instructionStepKeys);
    const filtered = new Set([...checkedSteps].filter((key) => validKeys.has(key)));
    if (filtered.size !== checkedSteps.size) {
      checkedSteps = filtered;
      persistInstructionChecks();
    }
  });

  function applyInstructionChecks() {
    if (!browser || !instructionsContainer) return;
    const items = instructionsContainer.querySelectorAll("li[data-step-key]");
    items.forEach((item) => {
      const key = item.getAttribute("data-step-key") ?? "";
      const isChecked = key ? checkedSteps.has(key) : false;
      item.setAttribute("data-step-checked", isChecked ? "true" : "false");
      const checkbox = item.querySelector<HTMLInputElement>("input.recipe-step-checkbox");
      if (checkbox) checkbox.checked = isChecked;
    });
  }

  $effect(() => {
    if (!browser || !instructionsContainer) return;
    const handleClick = (event: Event) => handleInstructionClick(event as MouseEvent);
    const handleChange = (event: Event) => handleInstructionChange(event);
    instructionsContainer.addEventListener("click", handleClick);
    instructionsContainer.addEventListener("change", handleChange);

    return () => {
      instructionsContainer?.removeEventListener("click", handleClick);
      instructionsContainer?.removeEventListener("change", handleChange);
    };
  });

  $effect(() => {
    if (!browser || !followAlongEnabled) return;
    const _ = instructionsHtml;
    const __ = checkedSteps;
    void (async () => {
      await tick();
      applyInstructionChecks();
    })();
  });

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
          <RecipeNutritionSheet recipe={scaledRecipe} />
          {#if data.can_edit}
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
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-200">Servings</span>
            <Input
              type="number"
              min="1"
              step="1"
              inputmode="numeric"
              aria-label="Servings"
              class="h-8 w-20 text-center text-sm"
              bind:value={servingsInput}
              onblur={normalizeServingsInput}
            />
            <span class="text-xs text-gray-500 dark:text-gray-400">Base {baseServings}</span>
            <span
              class="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-200"
            >
              x{formatAmount(scaleFactor)}
            </span>
          </div>
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
              {scaledRecipe.total_calories || 0}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Total Calories</div>
            <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {scaledRecipe.calories_per_100g || 0} cal/100g
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
              {scaledRecipe.calories_per_serving || 0}
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
              {scaledRecipe.calculated_weight || 0}g
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
              {scaledIngredients.length}
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
              <Button
                variant={followAlongEnabled ? "primary" : "outline"}
                size="sm"
                aria-pressed={followAlongEnabled}
                onclick={() => setFollowAlongEnabled(!followAlongEnabled)}
              >
                {followAlongEnabled ? "Follow Along: On" : "Follow Along"}
              </Button>
            </div>

            <div class="prose prose-lg dark:prose-invert recipe-instructions max-w-none">
              <div
                bind:this={instructionsContainer}
                class={followAlongEnabled ? "follow-along" : ""}
              >
                {@html instructionsHtml}
              </div>
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
        <RecipeIngredientsChecklist ingredients={scaledIngredients} recipeId={data.recipe.id} />

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
                    Scale x{formatAmount(subRecipeLink.scale_factor)} •
                    {formatAmount(subRecipeLink.scaled_servings)} servings
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

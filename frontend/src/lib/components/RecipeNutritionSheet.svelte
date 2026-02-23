<script lang="ts">
  import * as Sheet from "$lib/components/ui/sheet";
  import type { RecipePublic } from "$lib/client";
  import { pie as d3Pie, arc as d3Arc } from "d3-shape";

  type IngredientNutritionRow = {
    id: string;
    title: string;
    amount: number;
    unit: string;
    grams: number;
    calories: number;
    carbohydrates: number;
    fat: number;
    protein: number;
    calorieShare: number;
    carbohydrateShare: number;
    fatShare: number;
    proteinShare: number;
  };

  type PieSlice = {
    key: "carbohydrates" | "fat" | "protein";
    label: string;
    color: string;
    value: number;
    percentage: number;
    path: string;
    labelX: number;
    labelY: number;
    showLabel: boolean;
  };

  type MacroContributor = {
    title: string;
    value: number;
    share: number;
  };

  let { recipe }: { recipe: RecipePublic } = $props();

  let open = $state(false);

  function amountToGrams(
    amount: number,
    unit: string | undefined,
    weightPerPiece: number | undefined
  ): number {
    const safeAmount = Number.isFinite(amount) ? amount : 0;
    const safeWeightPerPiece = Number.isFinite(weightPerPiece) ? (weightPerPiece ?? 0) : 0;

    if (unit === "kg" || unit === "L") {
      return safeAmount * 1000;
    }

    if (unit === "pcs") {
      return safeAmount * safeWeightPerPiece;
    }

    return safeAmount;
  }

  function roundWhole(value: number | undefined): number {
    return Math.round(value ?? 0);
  }

  function roundOne(value: number): number {
    return Math.round(value * 10) / 10;
  }

  function topContributors(
    rows: IngredientNutritionRow[],
    field: "carbohydrates" | "fat" | "protein",
    total: number
  ): MacroContributor[] {
    return [...rows]
      .filter((row) => row[field] > 0)
      .sort((a, b) => b[field] - a[field])
      .slice(0, 4)
      .map((row) => ({
        title: row.title,
        value: row[field],
        share: total > 0 ? (row[field] / total) * 100 : 0
      }));
  }

  const ingredientRows = $derived.by<IngredientNutritionRow[]>(() => {
    const baseRows = recipe.ingredient_links.map((link) => {
      const grams = amountToGrams(
        link.amount ?? 0,
        link.unit ?? "g",
        link.ingredient.weight_per_piece ?? 0
      );
      const calories = (link.ingredient.calories * grams) / 100;
      const carbohydrates = (link.ingredient.carbohydrates * grams) / 100;
      const fat = (link.ingredient.fat * grams) / 100;
      const protein = (link.ingredient.protein * grams) / 100;

      return {
        id: link.ingredient.id,
        title: link.ingredient.title,
        amount: link.amount ?? 0,
        unit: link.unit ?? "g",
        grams,
        calories,
        carbohydrates,
        fat,
        protein,
        calorieShare: 0,
        carbohydrateShare: 0,
        fatShare: 0,
        proteinShare: 0
      };
    });

    const totalCalories = baseRows.reduce((sum, row) => sum + row.calories, 0);
    const totalCarbs = baseRows.reduce((sum, row) => sum + row.carbohydrates, 0);
    const totalFat = baseRows.reduce((sum, row) => sum + row.fat, 0);
    const totalProtein = baseRows.reduce((sum, row) => sum + row.protein, 0);

    return baseRows
      .map((row) => ({
        ...row,
        calorieShare: totalCalories > 0 ? (row.calories / totalCalories) * 100 : 0,
        carbohydrateShare: totalCarbs > 0 ? (row.carbohydrates / totalCarbs) * 100 : 0,
        fatShare: totalFat > 0 ? (row.fat / totalFat) * 100 : 0,
        proteinShare: totalProtein > 0 ? (row.protein / totalProtein) * 100 : 0
      }))
      .sort((a, b) => b.calories - a.calories);
  });

  const totalMacroGrams = $derived.by(
    () =>
      Math.max(recipe.total_carbohydrates ?? 0, 0) +
      Math.max(recipe.total_fat ?? 0, 0) +
      Math.max(recipe.total_protein ?? 0, 0)
  );

  const pieSlices = $derived.by<PieSlice[]>(() => {
    const rawSlices = [
      {
        key: "carbohydrates" as const,
        label: "Carbs",
        color: "#2563eb",
        value: Math.max(recipe.total_carbohydrates ?? 0, 0)
      },
      {
        key: "fat" as const,
        label: "Fat",
        color: "#d97706",
        value: Math.max(recipe.total_fat ?? 0, 0)
      },
      {
        key: "protein" as const,
        label: "Protein",
        color: "#dc2626",
        value: Math.max(recipe.total_protein ?? 0, 0)
      }
    ];

    const pieGenerator = d3Pie<(typeof rawSlices)[number]>()
      .value((slice) => slice.value)
      .padAngle(0.012)
      .sort(null);
    const pieData = pieGenerator(rawSlices);
    const arcGenerator = d3Arc<(typeof pieData)[number]>()
      .innerRadius(46)
      .outerRadius(88)
      .cornerRadius(5);
    const labelArc = d3Arc<(typeof pieData)[number]>().innerRadius(64).outerRadius(64);

    return pieData.map((segment) => {
      const slice = segment.data;
      const percentage = totalMacroGrams > 0 ? (slice.value / totalMacroGrams) * 100 : 0;
      const path = arcGenerator(segment) ?? "";
      const [labelX, labelY] = labelArc.centroid(segment);
      const showLabel = percentage >= 5 && slice.value > 0;

      return {
        ...slice,
        percentage,
        path,
        labelX,
        labelY,
        showLabel
      };
    });
  });

  const topCarbSources = $derived.by(() =>
    topContributors(ingredientRows, "carbohydrates", recipe.total_carbohydrates ?? 0)
  );
  const topFatSources = $derived.by(() =>
    topContributors(ingredientRows, "fat", recipe.total_fat ?? 0)
  );
  const topProteinSources = $derived.by(() =>
    topContributors(ingredientRows, "protein", recipe.total_protein ?? 0)
  );
</script>

<Sheet.Root bind:open>
  <Sheet.Trigger
    class="inline-flex items-center rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-900/40 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
  >
    Nutrition Deep Dive
  </Sheet.Trigger>

  <Sheet.Content side="right" class="w-full overflow-y-auto px-5 sm:max-w-4xl">
    <div class="space-y-8 pb-8">
      <div>
        <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Nutrition Deep Dive
        </h2>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-300">
          Breakdown of calories and macros for <span class="font-semibold">{recipe.title}</span>.
        </p>
      </div>

      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div
          class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900/40"
        >
          <p class="text-xs text-gray-500 dark:text-gray-400">Total Calories</p>
          <p class="text-xl font-bold text-gray-900 dark:text-gray-100">{recipe.total_calories}</p>
        </div>
        <div
          class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900/40"
        >
          <p class="text-xs text-gray-500 dark:text-gray-400">Per Serving</p>
          <p class="text-xl font-bold text-gray-900 dark:text-gray-100">
            {recipe.calories_per_serving}
          </p>
        </div>
        <div
          class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900/40"
        >
          <p class="text-xs text-gray-500 dark:text-gray-400">Total Weight</p>
          <p class="text-xl font-bold text-gray-900 dark:text-gray-100">
            {recipe.calculated_weight}g
          </p>
        </div>
        <div
          class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900/40"
        >
          <p class="text-xs text-gray-500 dark:text-gray-400">Calories / 100g</p>
          <p class="text-xl font-bold text-gray-900 dark:text-gray-100">
            {recipe.calories_per_100g}
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div
          class="rounded-lg border border-blue-200 bg-blue-50/80 p-3 dark:border-blue-900/40 dark:bg-blue-900/20"
        >
          <p class="text-xs text-blue-800 dark:text-blue-300">Carbohydrates</p>
          <p class="text-2xl font-bold text-blue-900 dark:text-blue-200">
            {roundWhole(recipe.total_carbohydrates)}g
          </p>
          <p class="text-xs text-blue-700 dark:text-blue-300/80">
            {roundWhole(recipe.carbohydrates_per_serving)}g / serving
          </p>
        </div>
        <div
          class="rounded-lg border border-amber-200 bg-amber-50/80 p-3 dark:border-amber-900/40 dark:bg-amber-900/20"
        >
          <p class="text-xs text-amber-800 dark:text-amber-300">Fat</p>
          <p class="text-2xl font-bold text-amber-900 dark:text-amber-200">
            {roundWhole(recipe.total_fat)}g
          </p>
          <p class="text-xs text-amber-700 dark:text-amber-300/80">
            {roundWhole(recipe.fat_per_serving)}g / serving
          </p>
        </div>
        <div
          class="rounded-lg border border-rose-200 bg-rose-50/80 p-3 dark:border-rose-900/40 dark:bg-rose-900/20"
        >
          <p class="text-xs text-rose-800 dark:text-rose-300">Protein</p>
          <p class="text-2xl font-bold text-rose-900 dark:text-rose-200">
            {roundWhole(recipe.total_protein)}g
          </p>
          <p class="text-xs text-rose-700 dark:text-rose-300/80">
            {roundWhole(recipe.protein_per_serving)}g / serving
          </p>
        </div>
      </div>

      <div
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/40"
      >
        <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          Macro Distribution
        </h3>
        <div class="grid items-center gap-6 lg:grid-cols-[260px_1fr]">
          <div class="mx-auto">
            {#if totalMacroGrams > 0}
              <svg viewBox="0 0 220 220" class="h-56 w-56">
                <g transform="translate(110, 110)">
                  {#each pieSlices as slice}
                    {#if slice.path}
                      <path d={slice.path} fill={slice.color} stroke="#0f172a" stroke-width="1.5"
                      ></path>
                      {#if slice.showLabel}
                        <text
                          x={slice.labelX}
                          y={slice.labelY}
                          text-anchor="middle"
                          dominant-baseline="middle"
                          class="fill-white text-[12px] font-semibold"
                        >
                          {roundWhole(slice.percentage)}%
                        </text>
                      {/if}
                    {/if}
                  {/each}
                  <circle r="37" fill="rgba(2, 6, 23, 0.9)"></circle>
                  <text
                    text-anchor="middle"
                    dominant-baseline="middle"
                    y="-11"
                    class="fill-slate-300 text-[8px] tracking-wide uppercase"
                  >
                    Total
                  </text>
                  <text
                    text-anchor="middle"
                    dominant-baseline="middle"
                    y="-2"
                    class="fill-slate-300 text-[8px] tracking-wide uppercase"
                  >
                    Macros
                  </text>
                  <text
                    text-anchor="middle"
                    dominant-baseline="middle"
                    y="13"
                    class="fill-white text-[14px] font-bold"
                  >
                    {roundWhole(totalMacroGrams)}g
                  </text>
                </g>
              </svg>
            {:else}
              <div
                class="flex h-56 w-56 items-center justify-center rounded-full border border-dashed border-gray-300 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400"
              >
                No macro data
              </div>
            {/if}
          </div>

          <div class="space-y-3">
            {#each pieSlices as slice}
              <div
                class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-800 dark:bg-gray-900/50"
              >
                <div class="flex items-center gap-2">
                  <span class="h-3 w-3 rounded-full" style={`background-color: ${slice.color}`}
                  ></span>
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-200"
                    >{slice.label}</span
                  >
                </div>
                <div class="text-right text-sm text-gray-700 dark:text-gray-300">
                  <div class="font-semibold">{roundWhole(slice.value)}g</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {roundWhole(slice.percentage)}%
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <div
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/40"
      >
        <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Macro Sources</h3>
        <div class="grid gap-4 md:grid-cols-3">
          <div
            class="rounded-lg border border-blue-200 bg-blue-50/70 p-3 dark:border-blue-900/30 dark:bg-blue-900/10"
          >
            <h4 class="mb-2 text-sm font-semibold text-blue-900 dark:text-blue-300">Carbs</h4>
            {#if topCarbSources.length > 0}
              <ul class="space-y-1.5">
                {#each topCarbSources as item}
                  <li class="flex items-center justify-between text-xs">
                    <span class="truncate text-blue-950 dark:text-blue-200">{item.title}</span>
                    <span class="text-blue-700 dark:text-blue-300">
                      {roundOne(item.value)}g ({roundOne(item.share)}%)
                    </span>
                  </li>
                {/each}
              </ul>
            {:else}
              <p class="text-xs text-blue-800/70 dark:text-blue-300/70">No carbohydrate sources</p>
            {/if}
          </div>

          <div
            class="rounded-lg border border-amber-200 bg-amber-50/70 p-3 dark:border-amber-900/30 dark:bg-amber-900/10"
          >
            <h4 class="mb-2 text-sm font-semibold text-amber-900 dark:text-amber-300">Fat</h4>
            {#if topFatSources.length > 0}
              <ul class="space-y-1.5">
                {#each topFatSources as item}
                  <li class="flex items-center justify-between text-xs">
                    <span class="truncate text-amber-950 dark:text-amber-200">{item.title}</span>
                    <span class="text-amber-700 dark:text-amber-300">
                      {roundOne(item.value)}g ({roundOne(item.share)}%)
                    </span>
                  </li>
                {/each}
              </ul>
            {:else}
              <p class="text-xs text-amber-800/70 dark:text-amber-300/70">No fat sources</p>
            {/if}
          </div>

          <div
            class="rounded-lg border border-rose-200 bg-rose-50/70 p-3 dark:border-rose-900/30 dark:bg-rose-900/10"
          >
            <h4 class="mb-2 text-sm font-semibold text-rose-900 dark:text-rose-300">Protein</h4>
            {#if topProteinSources.length > 0}
              <ul class="space-y-1.5">
                {#each topProteinSources as item}
                  <li class="flex items-center justify-between text-xs">
                    <span class="truncate text-rose-950 dark:text-rose-200">{item.title}</span>
                    <span class="text-rose-700 dark:text-rose-300">
                      {roundOne(item.value)}g ({roundOne(item.share)}%)
                    </span>
                  </li>
                {/each}
              </ul>
            {:else}
              <p class="text-xs text-rose-800/70 dark:text-rose-300/70">No protein sources</p>
            {/if}
          </div>
        </div>
      </div>

      <div
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900/40"
      >
        <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          Calories and Macros by Ingredient
        </h3>
        <div class="overflow-x-auto">
          <table class="min-w-full border-separate border-spacing-y-2 text-sm">
            <thead>
              <tr class="text-left text-xs text-gray-500 uppercase dark:text-gray-400">
                <th class="px-3 py-1">Ingredient</th>
                <th class="px-3 py-1">Used</th>
                <th class="px-3 py-1">Calories</th>
                <th class="px-3 py-1">Carbs</th>
                <th class="px-3 py-1">Fat</th>
                <th class="px-3 py-1">Protein</th>
                <th class="px-3 py-1">Cal Share</th>
              </tr>
            </thead>
            <tbody>
              {#each ingredientRows as row}
                <tr class="rounded-lg bg-gray-50 dark:bg-gray-900/50">
                  <td class="rounded-l-lg px-3 py-2 font-medium text-gray-900 dark:text-gray-100">
                    {row.title}
                  </td>
                  <td class="px-3 py-2 text-gray-700 dark:text-gray-300">
                    {roundOne(row.amount)}
                    {row.unit}
                    <span class="ml-1 text-xs text-gray-500 dark:text-gray-400">
                      ({roundWhole(row.grams)}g)
                    </span>
                  </td>
                  <td class="px-3 py-2 text-gray-700 dark:text-gray-300"
                    >{roundWhole(row.calories)} kcal</td
                  >
                  <td class="px-3 py-2 text-gray-700 dark:text-gray-300"
                    >{roundOne(row.carbohydrates)}g</td
                  >
                  <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{roundOne(row.fat)}g</td>
                  <td class="px-3 py-2 text-gray-700 dark:text-gray-300"
                    >{roundOne(row.protein)}g</td
                  >
                  <td class="rounded-r-lg px-3 py-2 text-gray-700 dark:text-gray-300">
                    {roundOne(row.calorieShare)}%
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </Sheet.Content>
</Sheet.Root>

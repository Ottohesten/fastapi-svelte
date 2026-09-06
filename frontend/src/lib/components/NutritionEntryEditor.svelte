<script lang="ts">
  import AlertCircle from "@lucide/svelte/icons/circle-alert";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import { Button } from "$lib/components/ui/button";
  import { Combobox } from "$lib/components/ui/combobox";
  import { Input } from "$lib/components/ui/input";
  import {
    draftIsComplete,
    draftPreview,
    formatNutrition,
    validProductUnits
  } from "$lib/nutrition/helpers";
  import {
    nutritionBasisLabels,
    sourceTypeLabels,
    type EntrySourceType,
    type EntryUnit,
    type NutritionEntryDraft,
    type NutritionIngredientOption,
    type NutritionProduct,
    type NutritionRecipeOption
  } from "$lib/nutrition/types";
  import type { NutritionBatchFormSchema, NutritionEntryFormSchema } from "$lib/schemas/nutrition";
  import { Control, Field, FieldErrors, Label } from "formsnap";
  import type { FormPath, Infer, SuperForm } from "sveltekit-superforms";

  type EntryFormController =
    | SuperForm<Infer<typeof NutritionEntryFormSchema>>
    | SuperForm<Infer<typeof NutritionBatchFormSchema>>;

  type Props = {
    form: EntryFormController;
    fieldPrefix?: `entries[${number}]`;
    entry: NutritionEntryDraft;
    recipes: NutritionRecipeOption[];
    products: NutritionProduct[];
    ingredients: NutritionIngredientOption[];
    removable?: boolean;
    onRemove?: () => void;
    showMeal?: boolean;
    showSourceSwitch?: boolean;
    onCatalogSelect?: (entry: NutritionEntryDraft) => void;
  };

  let {
    form,
    fieldPrefix,
    entry = $bindable(),
    recipes,
    products,
    ingredients,
    removable = false,
    onRemove,
    showMeal = true,
    showSourceSwitch = true,
    onCatalogSelect
  }: Props = $props();

  // Formsnap's generic path cannot express a prefix chosen at runtime. Both possible form
  // shapes are schema-backed above, so the cast is kept at this component boundary.
  const fieldForm = $derived(form as unknown as SuperForm<Record<string, unknown>>);
  function fieldName(field: keyof NutritionEntryDraft): FormPath<Record<string, unknown>> {
    return `${fieldPrefix ? `${fieldPrefix}.` : ""}${field}` as FormPath<Record<string, unknown>>;
  }

  const preview = $derived(draftPreview(entry));
  const complete = $derived(draftIsComplete(entry, recipes, products, ingredients));
  const selectedRecipe = $derived(recipes.find((recipe) => recipe.id === entry.source_id));
  const selectedProduct = $derived(products.find((product) => product.id === entry.source_id));
  const selectedIngredient = $derived(
    ingredients.find((ingredient) => ingredient.id === entry.source_id)
  );
  const hasSelectedCatalogFood = $derived(
    entry.source_type === "recipe"
      ? Boolean(selectedRecipe)
      : entry.source_type === "product"
        ? Boolean(selectedProduct)
        : entry.source_type === "ingredient"
          ? Boolean(selectedIngredient)
          : false
  );
  const selectedCatalogValue = $derived(
    hasSelectedCatalogFood ? `${entry.source_type}:${entry.source_id}` : ""
  );
  const catalogItems = $derived.by(() =>
    [
      ...recipes.map((recipe) => ({
        value: `recipe:${recipe.id}`,
        label: `${recipe.title} · Recipe`,
        description:
          recipe.serving_weight_grams > 0
            ? `${formatNutrition(recipe.calories)} kcal/serving · ${formatNutrition(recipe.serving_weight_grams)} g/serving`
            : `${formatNutrition(recipe.calories)} kcal/serving`,
        keywords: [recipe.title, "recipe"]
      })),
      ...products.map((product) => ({
        value: `product:${product.id}`,
        label: `${product.title}${product.brand ? ` — ${product.brand}` : ""} · Product`,
        description: `${formatNutrition(product.calories)} kcal ${nutritionBasisLabels[product.nutrition_basis ?? "per_100g"]}`,
        keywords: [product.title, product.brand ?? "", product.barcode ?? "", "product"]
      })),
      ...ingredients.map((ingredient) => ({
        value: `ingredient:${ingredient.id}`,
        label: `${ingredient.title} · Ingredient`,
        description: `${formatNutrition(ingredient.calories)} kcal/100 g`,
        keywords: [ingredient.title, "ingredient"]
      }))
    ].sort((left, right) => left.label.localeCompare(right.label, "en", { sensitivity: "base" }))
  );
  const selectedFoodDetails = $derived.by(() => {
    if (selectedRecipe) {
      const details = [`${formatNutrition(selectedRecipe.calories)} kcal per serving`];
      if (selectedRecipe.serving_weight_grams > 0) {
        details.push(`${formatNutrition(selectedRecipe.serving_weight_grams)} g per serving`);
      }
      details.push(
        `Full recipe makes ${selectedRecipe.servings} ${selectedRecipe.servings === 1 ? "serving" : "servings"}`
      );
      return details;
    }
    if (selectedProduct) {
      const basis = selectedProduct.nutrition_basis ?? "per_100g";
      const details = [
        `${formatNutrition(selectedProduct.calories)} kcal ${nutritionBasisLabels[basis]}`
      ];
      if (selectedProduct.serving_size && selectedProduct.serving_size_unit) {
        details.push(
          `Serving: ${formatNutrition(selectedProduct.serving_size)} ${selectedProduct.serving_size_unit}`
        );
      }
      if (selectedProduct.package_size && selectedProduct.package_size_unit) {
        details.push(
          `Package: ${formatNutrition(selectedProduct.package_size)} ${selectedProduct.package_size_unit}`
        );
      }
      return details;
    }
    if (selectedIngredient) {
      const details = [`${formatNutrition(selectedIngredient.calories)} kcal per 100 g`];
      if (selectedIngredient.weight_per_piece) {
        details.push(`1 piece is about ${formatNutrition(selectedIngredient.weight_per_piece)} g`);
      }
      return details;
    }
    return [];
  });

  const productUnits = $derived.by<EntryUnit[]>(() => {
    if (!selectedProduct) return ["g"];
    return validProductUnits(selectedProduct);
  });

  function markPreviewStale(next: NutritionEntryDraft): NutritionEntryDraft {
    return next.source_type === "manual" ? next : { ...next, preview: null };
  }

  function resetSource(sourceType: EntrySourceType) {
    entry = {
      ...entry,
      source_type: sourceType,
      source_id: "",
      title: "",
      unit: sourceType === "recipe" ? "serving" : sourceType === "manual" ? "piece" : "g",
      quantity: 1,
      status: sourceType === "manual" ? "needs_nutrition" : "resolved",
      preview: null,
      candidates: [],
      row_message: null,
      brand: "",
      calories: null,
      carbohydrates: null,
      fat: null,
      protein: null
    };
  }

  function enterManualFood() {
    resetSource("manual");
  }

  function enterCatalogFood() {
    resetSource("recipe");
  }

  function nullableNumber(event: Event): number | null {
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    return Number.isFinite(value) ? value : null;
  }

  function updateNutrition(field: "calories" | "carbohydrates" | "fat" | "protein", event: Event) {
    const value = nullableNumber(event);
    entry = {
      ...entry,
      [field]: value,
      status:
        entry.title.trim() && (field === "calories" ? value !== null : entry.calories !== null)
          ? "resolved"
          : "needs_nutrition"
    };
  }

  function chooseCatalogSource(catalogValue: string) {
    const separator = catalogValue.indexOf(":");
    if (separator === -1) return;

    const sourceType = catalogValue.slice(0, separator);
    const sourceId = catalogValue.slice(separator + 1);
    if (sourceType !== "recipe" && sourceType !== "product" && sourceType !== "ingredient") {
      return;
    }

    const source =
      sourceType === "recipe"
        ? recipes.find((item) => item.id === sourceId)
        : sourceType === "product"
          ? products.find((item) => item.id === sourceId)
          : ingredients.find((item) => item.id === sourceId);
    if (!source) return;
    chooseCandidate(sourceType, sourceId, source.title);
  }

  function chooseCandidate(
    sourceType: Exclude<EntrySourceType, "manual">,
    sourceId: string,
    title: string
  ) {
    const product = products.find((item) => item.id === sourceId);
    const ingredient = ingredients.find((item) => item.id === sourceId);
    const validUnits: EntryUnit[] =
      sourceType === "recipe"
        ? ["serving"]
        : sourceType === "product" && product
          ? validProductUnits(product)
          : sourceType === "ingredient" && ingredient?.weight_per_piece
            ? ["g", "piece"]
            : ["g"];
    entry = {
      ...entry,
      source_type: sourceType,
      source_id: sourceId,
      title,
      brand: product?.brand ?? "",
      unit: validUnits.includes(entry.unit) ? entry.unit : (validUnits[0] ?? "g"),
      status: "resolved",
      preview: null,
      candidates: [],
      row_message: null
    };
    onCatalogSelect?.(entry);
  }

  function updateQuantity(value: number) {
    entry = markPreviewStale({
      ...entry,
      quantity: value,
      status: Number.isFinite(value) && value > 0 && entry.source_id ? "resolved" : entry.status
    });
  }

  function updateUnit(unit: EntryUnit) {
    entry = markPreviewStale({
      ...entry,
      unit,
      status: entry.source_id && entry.quantity > 0 ? "resolved" : entry.status
    });
  }
</script>

<div class="space-y-4" data-entry-editor>
  {#if entry.original_text}
    <div class="bg-muted/50 rounded-lg px-3 py-2 text-sm">
      <span class="text-muted-foreground">From:</span>
      <span class="ml-1 font-medium">{entry.original_text}</span>
    </div>
  {/if}

  {#if entry.status !== "resolved" && !complete}
    <div
      class="flex gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-100"
    >
      <AlertCircle class="mt-0.5 size-4 shrink-0" />
      <div class="min-w-0">
        <p class="font-medium">
          {entry.status === "ambiguous" ? "Choose the food you meant" : "This food needs details"}
        </p>
        <p class="mt-0.5 text-xs opacity-80">
          {entry.row_message ?? "Nothing is saved until every item is resolved."}
        </p>
      </div>
    </div>
  {/if}

  {#if entry.candidates.length > 0 && entry.status !== "resolved" && !complete}
    <div class="flex flex-wrap gap-2">
      {#each entry.candidates as candidate (`${candidate.source_type}:${candidate.source_id}`)}
        <Button
          size="sm"
          variant="outline"
          onclick={() =>
            chooseCandidate(candidate.source_type, candidate.source_id, candidate.title)}
        >
          {candidate.title}
          <span class="text-muted-foreground text-xs"
            >({sourceTypeLabels[candidate.source_type]})</span
          >
        </Button>
      {/each}
    </div>
  {/if}

  {#if showMeal}
    <div class="max-w-xs min-w-0 space-y-2">
      <Field form={fieldForm} name={fieldName("meal_type")}>
        <Control>
          {#snippet children({ props })}
            <Label>Meal</Label>
            <select
              {...props}
              value={entry.meal_type}
              onchange={(event) =>
                (entry = {
                  ...entry,
                  meal_type: event.currentTarget.value as typeof entry.meal_type
                })}
              class="border-input bg-background focus-visible:ring-ring h-10 w-full rounded-md border px-3 text-sm focus-visible:ring-2 focus-visible:outline-none"
            >
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="dinner">Dinner</option>
              <option value="snack">Snack</option>
            </select>
          {/snippet}
        </Control>
        <FieldErrors />
      </Field>
    </div>
  {/if}

  {#if entry.source_type !== "manual"}
    <div
      class={hasSelectedCatalogFood
        ? entry.source_type === "recipe"
          ? "grid gap-4 sm:grid-cols-[minmax(0,1fr)_9rem]"
          : "grid gap-4 sm:grid-cols-[minmax(0,1fr)_8rem_8rem]"
        : "grid gap-4"}
    >
      <div class="min-w-0 space-y-2">
        <Field form={fieldForm} name={fieldName("source_id")}>
          <Control>
            {#snippet children({ props })}
              <Label>Saved food</Label>
              <Combobox
                controlProps={props}
                items={catalogItems}
                value={selectedCatalogValue}
                onSelect={(item) => item && chooseCatalogSource(item.value)}
                placeholder="Search recipes, products, and ingredients…"
                searchPlaceholder="Search all saved foods…"
                emptyMessage="No matching saved food found."
                ariaLabel="Saved food"
                buttonClass="w-full justify-between"
                popoverClass="w-(--bits-popover-anchor-width) sm:min-w-[28rem]"
              />
            {/snippet}
          </Control>
          <p class="text-muted-foreground text-xs">
            Search recipes, packaged products, and ingredients together.
          </p>
          <FieldErrors />
        </Field>
      </div>

      {#if hasSelectedCatalogFood}
        <div class="min-w-0 space-y-2">
          <Field form={fieldForm} name={fieldName("quantity")}>
            <Control>
              {#snippet children({ props })}
                <Label>{entry.source_type === "recipe" ? "Servings" : "Amount"}</Label>
                <Input
                  {...props}
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={entry.quantity}
                  oninput={(event) => updateQuantity(event.currentTarget.valueAsNumber)}
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </Field>
        </div>

        {#if entry.source_type !== "recipe"}
          <div class="min-w-0 space-y-2">
            <Field form={fieldForm} name={fieldName("unit")}>
              <Control>
                {#snippet children({ props })}
                  <Label>Unit</Label>
                  <select
                    {...props}
                    value={entry.unit}
                    onchange={(event) => updateUnit(event.currentTarget.value as EntryUnit)}
                    class="border-input bg-background focus-visible:ring-ring h-10 w-full rounded-md border px-3 text-sm focus-visible:ring-2 focus-visible:outline-none"
                  >
                    {#if entry.source_type === "product"}
                      {#each productUnits as unit}
                        <option value={unit}>{unit}</option>
                      {/each}
                    {:else}
                      <option value="g">g</option>
                      {#if selectedIngredient?.weight_per_piece}
                        <option value="piece">piece</option>
                      {/if}
                    {/if}
                  </select>
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
          </div>
        {/if}
      {/if}
    </div>

    {#if selectedFoodDetails.length > 0}
      <div
        class="bg-muted/45 text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 rounded-lg px-3 py-2 text-xs"
        data-food-details
      >
        {#each selectedFoodDetails as detail}
          <span>{detail}</span>
        {/each}
      </div>
    {/if}

    {#if showSourceSwitch}
      <div class="flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-muted-foreground text-sm">Can’t find it in your saved foods?</p>
        <Button type="button" variant="outline" onclick={enterManualFood}>
          Enter a one-off food
        </Button>
      </div>
    {/if}
  {:else}
    <div class="space-y-4 rounded-lg border p-4">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="font-medium">One-off food</p>
          <p class="text-muted-foreground text-sm">
            Enter the nutrition totals for this complete entry.
          </p>
        </div>
        {#if showSourceSwitch}
          <Button type="button" variant="outline" size="sm" onclick={enterCatalogFood}>
            Search saved foods instead
          </Button>
        {/if}
      </div>
      <div class="min-w-0 space-y-2">
        <Field form={fieldForm} name={fieldName("title")}>
          <Control>
            {#snippet children({ props })}
              <Label>Description</Label>
              <Input
                {...props}
                value={entry.title}
                placeholder="e.g. a slice of birthday cake"
                oninput={(event) => {
                  const title = event.currentTarget.value;
                  entry = {
                    ...entry,
                    title,
                    status: title.trim() && entry.calories !== null ? "resolved" : "needs_nutrition"
                  };
                }}
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>
      </div>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div class="min-w-0 space-y-2">
          <Field form={fieldForm} name={fieldName("calories")}>
            <Control>
              {#snippet children({ props })}
                <Label>Calories</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  value={entry.calories ?? ""}
                  oninput={(event) => updateNutrition("calories", event)}
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </Field>
        </div>
        <div class="min-w-0 space-y-2">
          <Field form={fieldForm} name={fieldName("carbohydrates")}>
            <Control>
              {#snippet children({ props })}
                <Label>Carbs (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  value={entry.carbohydrates ?? ""}
                  oninput={(event) => updateNutrition("carbohydrates", event)}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </Field>
        </div>
        <div class="min-w-0 space-y-2">
          <Field form={fieldForm} name={fieldName("fat")}>
            <Control>
              {#snippet children({ props })}
                <Label>Fat (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  value={entry.fat ?? ""}
                  oninput={(event) => updateNutrition("fat", event)}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </Field>
        </div>
        <div class="min-w-0 space-y-2">
          <Field form={fieldForm} name={fieldName("protein")}>
            <Control>
              {#snippet children({ props })}
                <Label>Protein (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  value={entry.protein ?? ""}
                  oninput={(event) => updateNutrition("protein", event)}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </Field>
        </div>
      </div>
    </div>
  {/if}

  {#if hasSelectedCatalogFood || entry.source_type === "manual" || removable}
    <div
      class="bg-muted/45 flex flex-wrap items-center gap-x-5 gap-y-1 rounded-lg px-3 py-2 text-sm"
    >
      {#if preview}
        <span class="font-semibold">{formatNutrition(preview.calories)} kcal</span>
        <span class="text-muted-foreground"
          >C {formatNutrition(preview.carbohydrates)}{preview.carbohydrates === null
            ? ""
            : "g"}</span
        >
        <span class="text-muted-foreground"
          >F {formatNutrition(preview.fat)}{preview.fat === null ? "" : "g"}</span
        >
        <span class="text-muted-foreground"
          >P {formatNutrition(preview.protein)}{preview.protein === null ? "" : "g"}</span
        >
      {:else if entry.source_type !== "manual" && entry.source_id}
        <span class="text-muted-foreground text-xs"
          >Nutrition will be calculated by the server when saved.</span
        >
      {/if}
      {#if !complete}
        <span class="text-destructive ml-auto text-xs font-medium"
          >Complete the required fields</span
        >
      {/if}
      {#if removable}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="text-destructive ml-auto"
          aria-label="Remove draft entry"
          onclick={onRemove}
        >
          <Trash2 /> Remove
        </Button>
      {/if}
    </div>
  {/if}
</div>

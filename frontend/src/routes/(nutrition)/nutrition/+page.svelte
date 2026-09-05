<script lang="ts">
  import { applyAction, enhance } from "$app/forms";
  import { goto, invalidateAll } from "$app/navigation";
  import { page } from "$app/stores";
  import { onMount, untrack } from "svelte";
  import type { SubmitFunction } from "@sveltejs/kit";
  import {
    CalendarDays,
    ChevronLeft,
    ChevronRight,
    CircleAlert,
    Flame,
    LoaderCircle,
    Pencil,
    Plus,
    Repeat2,
    Sparkles,
    Trash2
  } from "@lucide/svelte";
  import type { NutritionCommonEntryPublic } from "$lib/client";
  import NutritionEntryEditor from "$lib/components/NutritionEntryEditor.svelte";
  import * as Alert from "$lib/components/ui/alert";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import {
    defaultMealType,
    draftIsComplete,
    formatNutrition,
    validProductUnits
  } from "$lib/nutrition/helpers";
  import {
    emptyNutritionTotals,
    mealTypeLabels,
    mealTypes,
    sourceTypeLabels,
    type EntrySourceType,
    type EntryUnit,
    type MealType,
    type NutritionEntry,
    type NutritionEntryDraft,
    type NutritionTotals
  } from "$lib/nutrition/types";
  import {
    NutritionBatchFormSchema,
    NutritionEntryFormSchema,
    NutritionMoveFormSchema,
    QuickAddFormSchema
  } from "$lib/schemas/nutrition";
  import { Control, Field, FieldErrors, Label } from "formsnap";
  import { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();

  let addOpen = $state(false);
  let editOpen = $state(false);
  let editReplacing = $state(false);
  let actionError = $state("");
  let successMessage = $state("");
  let quickServerCanConfirm = $state(false);

  const entryForm = superForm(
    untrack(() => data.entryForm),
    {
      id: "nutritionEntryForm",
      validators: zodClient(NutritionEntryFormSchema),
      dataType: "json",
      invalidateAll: false,
      resetForm: false,
      onSubmit: () => {
        actionError = "";
        successMessage = "";
      },
      onResult: async ({ result }) => {
        if (result.type === "success") {
          const updated = Boolean($entryData.id);
          addOpen = false;
          editOpen = false;
          successMessage = updated ? "Diary entry updated." : "Food added to the diary.";
          await invalidateAll();
        } else if (result.type === "failure") {
          actionError = resultMessage(result.data);
        }
      }
    }
  );

  const quickAddForm = superForm(
    untrack(() => data.quickAddForm),
    {
      id: "quickAddForm",
      validators: zodClient(QuickAddFormSchema),
      dataType: "json",
      invalidateAll: false,
      resetForm: false,
      onSubmit: () => {
        actionError = "";
        successMessage = "";
      },
      onResult: ({ result }) => {
        if (result.type === "success") {
          const payload = result.data as {
            previewRows?: NutritionEntryDraft[];
            canConfirm?: boolean;
          };
          $batchData.entries = payload.previewRows ?? [];
          quickServerCanConfirm = payload.canConfirm ?? false;
        } else if (result.type === "failure") {
          $batchData.entries = [];
          quickServerCanConfirm = false;
          actionError = resultMessage(result.data);
        }
      }
    }
  );

  const batchForm = superForm(
    untrack(() => data.batchForm),
    {
      id: "nutritionBatchForm",
      validators: zodClient(NutritionBatchFormSchema),
      dataType: "json",
      invalidateAll: false,
      resetForm: false,
      onSubmit: () => {
        actionError = "";
        successMessage = "";
      },
      onUpdated: async ({ form }) => {
        if (typeof form.message !== "string") return;
        if (form.valid) {
          $batchData.entries = [];
          quickAddForm.reset({
            data: {
              text: "",
              log_date: data.selectedDate,
              default_meal: $quickData.default_meal
            }
          });
          quickServerCanConfirm = false;
          successMessage = "Reviewed foods added to the diary.";
          await invalidateAll();
        } else {
          actionError = form.message;
        }
      }
    }
  );

  const moveForm = superForm(
    untrack(() => data.moveForm),
    {
      id: "nutritionMoveForm",
      validators: zodClient(NutritionMoveFormSchema),
      dataType: "json",
      invalidateAll: false,
      resetForm: false,
      onSubmit: () => {
        actionError = "";
        successMessage = "";
      },
      onResult: async ({ result }) => {
        if (result.type === "success") {
          editOpen = false;
          successMessage = "Diary entry updated.";
          await invalidateAll();
        } else if (result.type === "failure") {
          actionError = resultMessage(result.data);
        }
      }
    }
  );

  const { form: entryData, enhance: entryEnhance, submitting: entrySubmitting } = entryForm;
  const { form: quickData, enhance: quickEnhance, submitting: quickSubmitting } = quickAddForm;
  const { form: batchData, enhance: batchEnhance, submitting: batchSubmitting } = batchForm;
  const { form: moveData, enhance: moveEnhance, submitting: moveSubmitting } = moveForm;

  function blankDraft(clientId: string, mealType: MealType = "snack"): NutritionEntryDraft {
    return {
      id: "",
      client_id: clientId,
      original_text: "",
      log_date: data.selectedDate,
      meal_type: mealType,
      source_type: "recipe",
      source_id: "",
      title: "",
      brand: "",
      note: "",
      quantity: 1,
      unit: "serving",
      status: "resolved",
      candidates: [],
      preview: null,
      calories: null,
      carbohydrates: null,
      fat: null,
      protein: null,
      row_message: null
    };
  }

  const entryComplete = $derived(
    draftIsComplete(
      $entryData,
      data.catalog.recipes,
      data.catalog.products,
      data.catalog.ingredients
    )
  );
  const quickComplete = $derived(
    $batchData.entries.length > 0 &&
      $batchData.entries.every((row) =>
        draftIsComplete(row, data.catalog.recipes, data.catalog.products, data.catalog.ingredients)
      )
  );
  const editComplete = $derived(
    draftIsComplete(
      $entryData,
      data.catalog.recipes,
      data.catalog.products,
      data.catalog.ingredients
    )
  );

  function localDateString(date = new Date()): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function shiftDate(date: string, days: number): string {
    const shifted = new Date(`${date}T12:00:00`);
    shifted.setDate(shifted.getDate() + days);
    return localDateString(shifted);
  }

  function dateHref(date: string): string {
    return `/nutrition?date=${encodeURIComponent(date)}`;
  }

  function readableDate(date: string): string {
    return new Intl.DateTimeFormat("en-DK", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric"
    }).format(new Date(`${date}T12:00:00`));
  }

  function resultMessage(data: Record<string, unknown> | undefined): string {
    if (!data) return "The request could not be completed.";
    if (typeof data.error === "string") return data.error;
    for (const value of Object.values(data)) {
      if (value && typeof value === "object" && "message" in value) {
        const formMessage = value.message;
        if (typeof formMessage === "string") return formMessage;
      }
    }
    return "Check the highlighted fields and try again.";
  }

  const deleteEnhance: SubmitFunction = () => {
    actionError = "";
    successMessage = "";
    return async ({ result }) => {
      if (result.type === "success") {
        successMessage = "Diary entry deleted.";
        await invalidateAll();
        return;
      }
      if (result.type === "failure") {
        actionError = resultMessage(result.data);
        return;
      }
      await applyAction(result);
    };
  };

  function startFoodAdd() {
    actionError = "";
    $entryData = blankDraft("manual-add", defaultMealType());
    addOpen = true;
  }

  function startCommonAdd(commonEntry: NutritionCommonEntryPublic) {
    actionError = "";
    const draft = blankDraft("common-add", defaultMealType());
    draft.source_type = commonEntry.source_type;
    draft.source_id = commonEntry.source_id ?? "";
    draft.title = commonEntry.title;
    draft.brand = commonEntry.brand ?? "";
    draft.quantity = commonEntry.quantity;
    draft.unit = commonEntry.unit;
    draft.status = "resolved";
    draft.calories = commonEntry.calories;
    draft.carbohydrates = commonEntry.carbohydrates;
    draft.fat = commonEntry.fat;
    draft.protein = commonEntry.protein;
    draft.preview = {
      calories: commonEntry.calories,
      carbohydrates: commonEntry.carbohydrates,
      fat: commonEntry.fat,
      protein: commonEntry.protein
    };
    $entryData = draft;
    addOpen = true;
  }

  function commonEntryKey(commonEntry: NutritionCommonEntryPublic): string {
    return [
      commonEntry.source_type,
      commonEntry.source_id ?? "",
      commonEntry.title,
      commonEntry.brand ?? "",
      commonEntry.quantity,
      commonEntry.unit,
      commonEntry.calories,
      commonEntry.carbohydrates ?? "unknown",
      commonEntry.fat ?? "unknown",
      commonEntry.protein ?? "unknown"
    ].join(":");
  }

  function commonEntryName(commonEntry: NutritionCommonEntryPublic): string {
    return commonEntry.brand ? `${commonEntry.title} — ${commonEntry.brand}` : commonEntry.title;
  }

  function startEdit(entry: NutritionEntry) {
    actionError = "";
    editReplacing = false;
    const logDate = entry.log_date.toISOString().slice(0, 10);
    $entryData = {
      id: entry.id,
      client_id: "entry-edit",
      original_text: "",
      log_date: logDate,
      meal_type: entry.meal_type,
      source_type: entry.source_type,
      source_id: entry.source_id ?? "",
      title: entry.title,
      brand: entry.brand ?? "",
      note: entry.note ?? "",
      quantity: entry.quantity,
      unit: entry.unit,
      status: entry.source_available || entry.source_type === "manual" ? "resolved" : "unmatched",
      candidates: [],
      preview: {
        calories: entry.calories,
        carbohydrates: entry.carbohydrates,
        fat: entry.fat,
        protein: entry.protein
      },
      calories: entry.calories,
      carbohydrates: entry.carbohydrates,
      fat: entry.fat,
      protein: entry.protein,
      row_message: entry.source_available
        ? null
        : "The original food was deleted. Choose a replacement."
    };
    $moveData = {
      id: entry.id,
      log_date: logDate,
      meal_type: entry.meal_type,
      note: entry.note ?? ""
    };
    editOpen = true;
  }

  function toggleEditMode() {
    if (!editReplacing) {
      $entryData.log_date = $moveData.log_date;
      $entryData.meal_type = $moveData.meal_type;
      $entryData.note = $moveData.note;
    } else {
      $moveData.log_date = $entryData.log_date;
      $moveData.meal_type = $entryData.meal_type;
      $moveData.note = $entryData.note;
    }
    editReplacing = !editReplacing;
  }

  function removeQuickRow(clientId: string) {
    $batchData.entries = $batchData.entries.filter((row) => row.client_id !== clientId);
  }

  function unknownMacro(totals: NutritionTotals, macro: "carbohydrates" | "fat" | "protein") {
    if (macro === "carbohydrates") return totals.carbohydrates_unknown ?? false;
    if (macro === "fat") return totals.fat_unknown ?? false;
    return totals.protein_unknown ?? false;
  }

  onMount(() => {
    $quickData.default_meal = defaultMealType();
    const browserToday = localDateString();
    if (!$page.url.searchParams.has("date") && browserToday !== data.selectedDate) {
      void goto(dateHref(browserToday), { replaceState: true });
      return;
    }

    const sourceType = data.prefill.sourceType;
    const sourceId = data.prefill.sourceId;
    if (
      sourceId &&
      (sourceType === "recipe" || sourceType === "product" || sourceType === "ingredient")
    ) {
      const draft = blankDraft("manual-add", defaultMealType());
      draft.source_type = sourceType as EntrySourceType;
      draft.source_id = sourceId;
      const selectedProduct = data.catalog.products.find((item) => item.id === sourceId);
      const fallbackUnit =
        sourceType === "recipe"
          ? "serving"
          : sourceType === "ingredient"
            ? "g"
            : selectedProduct?.nutrition_basis === "per_100ml"
              ? "ml"
              : selectedProduct?.nutrition_basis === "per_serving"
                ? "serving"
                : selectedProduct?.nutrition_basis === "per_package"
                  ? "package"
                  : "g";
      const requestedUnit = data.prefill.unit;
      const validUnits: readonly EntryUnit[] =
        sourceType === "product" && selectedProduct
          ? validProductUnits(selectedProduct)
          : sourceType === "recipe"
            ? ["serving"]
            : ["g", "piece"];
      draft.unit = validUnits.includes(requestedUnit as EntryUnit)
        ? (requestedUnit as EntryUnit)
        : validUnits.includes(fallbackUnit)
          ? fallbackUnit
          : (validUnits[0] ?? fallbackUnit);
      const quantity = Number(data.prefill.quantity ?? "1");
      draft.quantity = Number.isFinite(quantity) && quantity > 0 ? quantity : 1;
      $entryData = draft;
      addOpen = true;
    }
  });
</script>

<svelte:head><title>Nutrition diary</title></svelte:head>

<div class="container mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
  <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <p class="text-primary text-sm font-semibold tracking-wide uppercase">Personal nutrition</p>
      <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">Food diary</h1>
      <p class="text-muted-foreground mt-2">
        Recipes, packaged products, and one-off foods in one day.
      </p>
    </div>
    <Button type="button" class="h-11 w-full sm:w-auto" onclick={startFoodAdd}>
      <Plus /> Add food
    </Button>
  </header>

  {#if actionError}
    <Alert.Root variant="destructive">
      <CircleAlert />
      <Alert.Title>Unable to save</Alert.Title>
      <Alert.Description>{actionError}</Alert.Description>
    </Alert.Root>
  {:else if successMessage}
    <Alert.Root>
      <Alert.Title>Done</Alert.Title>
      <Alert.Description>{successMessage}</Alert.Description>
    </Alert.Root>
  {/if}

  <Card.Root>
    <Card.Content class="flex flex-col gap-3 pt-6 sm:flex-row sm:items-center sm:justify-between">
      <Button href={dateHref(shiftDate(data.selectedDate, -1))} variant="outline" class="h-11">
        <ChevronLeft /> Previous
      </Button>
      <div class="text-center">
        <div class="flex items-center justify-center gap-2 font-semibold">
          <CalendarDays class="size-5" />
          {readableDate(data.selectedDate)}
        </div>
        {#if data.selectedDate !== localDateString()}
          <a
            class="text-primary mt-1 inline-block text-sm hover:underline"
            href={dateHref(localDateString())}
          >
            Go to today
          </a>
        {/if}
      </div>
      <Button href={dateHref(shiftDate(data.selectedDate, 1))} variant="outline" class="h-11">
        Next <ChevronRight />
      </Button>
    </Card.Content>
  </Card.Root>

  <section aria-label="Daily nutrition" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
    <Card.Root
      class="col-span-2 border-orange-200 bg-orange-50/60 lg:col-span-1 dark:border-orange-950 dark:bg-orange-950/20"
    >
      <Card.Content class="pt-5">
        <div class="text-muted-foreground flex items-center gap-2 text-sm">
          <Flame class="size-4" /> Calories
        </div>
        <p class="mt-2 text-3xl font-bold">{formatNutrition(data.day.totals.calories)}</p>
        <p class="text-muted-foreground text-xs">kcal today</p>
      </Card.Content>
    </Card.Root>
    {#each ["carbohydrates", "fat", "protein"] as macro}
      <Card.Root>
        <Card.Content class="pt-5">
          <div class="flex items-center justify-between gap-2">
            <span class="text-muted-foreground text-sm capitalize">{macro}</span>
            {#if unknownMacro(data.day.totals, macro as "carbohydrates" | "fat" | "protein")}
              <Badge variant="outline" class="text-[10px]">Incomplete</Badge>
            {/if}
          </div>
          <p class="mt-2 text-2xl font-bold">
            {formatNutrition(data.day.totals[macro as "carbohydrates" | "fat" | "protein"])}g
          </p>
        </Card.Content>
      </Card.Root>
    {/each}
  </section>

  <Card.Root class="border-primary/20 overflow-hidden">
    <Card.Header>
      <div class="flex items-start gap-3">
        <span class="bg-primary/10 text-primary grid size-10 shrink-0 place-items-center rounded-xl"
          ><Sparkles class="size-5" /></span
        >
        <div>
          <Card.Title>Quick add</Card.Title>
          <Card.Description
            >One food per line. English and Danish names and meal headings work.</Card.Description
          >
        </div>
      </div>
    </Card.Header>
    <Card.Content class="space-y-4">
      <form method="POST" action="?/preview" use:quickEnhance class="space-y-4">
        <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_12rem]">
          <Field form={quickAddForm} name="text">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>What did you eat?</Label>
                  <textarea
                    {...props}
                    bind:value={$quickData.text}
                    rows="5"
                    class="border-input bg-background focus-visible:ring-ring min-h-32 w-full rounded-md border px-3 py-2 text-base focus-visible:ring-2 focus-visible:outline-none"
                    placeholder={"Breakfast:\n2 servings oatmeal\nproduct: half package frozen pizza\nmanual: birthday cake | 320 kcal"}
                  ></textarea>
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
          <Field form={quickAddForm} name="default_meal">
            <div class="space-y-2 md:self-start">
              <Control>
                {#snippet children({ props })}
                  <Label>Default meal</Label>
                  <select
                    {...props}
                    bind:value={$quickData.default_meal}
                    class="border-input bg-background h-11 w-full rounded-md border px-3"
                  >
                    {#each mealTypes as meal}
                      <option value={meal}>{mealTypeLabels[meal]}</option>
                    {/each}
                  </select>
                {/snippet}
              </Control>
              <p class="text-muted-foreground text-xs">Meal headings in the text override this.</p>
              <FieldErrors />
            </div>
          </Field>
        </div>
        <Button
          type="submit"
          variant="secondary"
          class="h-11 w-full sm:w-auto"
          disabled={$quickSubmitting}
        >
          {#if $quickSubmitting}<LoaderCircle class="animate-spin" />{:else}<Sparkles />{/if}
          Review entries
        </Button>
      </form>

      {#if $batchData.entries.length > 0}
        <div class="space-y-4 border-t pt-5">
          <div>
            <h2 class="font-semibold">Review before saving</h2>
            <p class="text-muted-foreground text-sm">
              Resolve every highlighted row. No entry has been saved yet.
            </p>
          </div>
          {#each $batchData.entries as row, index (row.client_id)}
            <div class="rounded-xl border p-4">
              <NutritionEntryEditor
                form={batchForm}
                fieldPrefix={`entries[${index}]`}
                bind:entry={$batchData.entries[index]}
                recipes={data.catalog.recipes}
                products={data.catalog.products}
                ingredients={data.catalog.ingredients}
                removable
                onRemove={() => removeQuickRow(row.client_id)}
              />
            </div>
          {/each}
          <form method="POST" action="?/batch" use:batchEnhance>
            <Button
              type="submit"
              class="h-11 w-full sm:w-auto"
              disabled={!quickComplete || $batchSubmitting}
            >
              {#if $batchSubmitting}<LoaderCircle class="animate-spin" />{/if}
              Add {$batchData.entries.length}
              {$batchData.entries.length === 1 ? "entry" : "entries"}
            </Button>
            {#if quickComplete && !quickServerCanConfirm}
              <p class="text-muted-foreground mt-2 text-xs">
                Your corrections will be validated again by the server.
              </p>
            {/if}
          </form>
        </div>
      {/if}
    </Card.Content>
  </Card.Root>

  <section aria-label="Meals" class="space-y-4">
    {#each mealTypes as mealType}
      {@const group = data.day.groups.find((item) => item.meal_type === mealType) ?? {
        meal_type: mealType,
        totals: emptyNutritionTotals(),
        entries: []
      }}
      <Card.Root>
        <Card.Header class="border-b">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <Card.Title><h2>{mealTypeLabels[mealType]}</h2></Card.Title>
              <Card.Description
                >{group.entries.length}
                {group.entries.length === 1 ? "entry" : "entries"}</Card.Description
              >
            </div>
            <div class="text-right">
              <p class="text-lg font-bold">{formatNutrition(group.totals.calories)} kcal</p>
              <p class="text-muted-foreground text-xs">
                C {formatNutrition(group.totals.carbohydrates)}g{unknownMacro(
                  group.totals,
                  "carbohydrates"
                )
                  ? "*"
                  : ""} · F {formatNutrition(group.totals.fat)}g{unknownMacro(group.totals, "fat")
                  ? "*"
                  : ""} · P {formatNutrition(group.totals.protein)}g{unknownMacro(
                  group.totals,
                  "protein"
                )
                  ? "*"
                  : ""}
              </p>
              {#if unknownMacro(group.totals, "carbohydrates") || unknownMacro(group.totals, "fat") || unknownMacro(group.totals, "protein")}
                <p class="text-muted-foreground text-[10px]">
                  * Known subtotal; some values unknown
                </p>
              {/if}
            </div>
          </div>
        </Card.Header>
        <Card.Content class="divide-y p-0">
          {#if group.entries.length === 0}
            <div class="text-muted-foreground px-6 py-8 text-center text-sm">
              Nothing logged yet.
            </div>
          {:else}
            {#each group.entries as entry (entry.id)}
              <article class="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:px-6">
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <h3 class="truncate font-medium">{entry.title}</h3>
                    <Badge variant="secondary">{sourceTypeLabels[entry.source_type]}</Badge>
                    {#if !entry.source_available && entry.source_type !== "manual"}
                      <Badge variant="outline">Source deleted</Badge>
                    {/if}
                  </div>
                  <p class="text-muted-foreground mt-1 text-sm">
                    {formatNutrition(entry.quantity)}
                    {entry.unit} · {formatNutrition(entry.calories)} kcal · C {formatNutrition(
                      entry.carbohydrates
                    )}{entry.carbohydrates === null ? "" : "g"}
                    · F {formatNutrition(entry.fat)}{entry.fat === null ? "" : "g"}
                    · P {formatNutrition(entry.protein)}{entry.protein === null ? "" : "g"}
                  </p>
                  {#if entry.note}<p class="text-muted-foreground mt-1 text-xs">
                      {entry.note}
                    </p>{/if}
                </div>
                <div class="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    class="h-10 flex-1 sm:flex-none"
                    onclick={() => startEdit(entry)}
                  >
                    <Pencil /> Edit
                  </Button>
                  <form
                    method="POST"
                    action="?/delete"
                    use:enhance={deleteEnhance}
                    onsubmit={(event) => {
                      if (!confirm(`Delete ${entry.title} from this day?`)) event.preventDefault();
                    }}
                  >
                    <input type="hidden" name="id" value={entry.id} />
                    <Button
                      type="submit"
                      variant="ghost"
                      size="sm"
                      class="text-destructive h-10"
                      aria-label={`Delete ${entry.title}`}
                    >
                      <Trash2 />
                    </Button>
                  </form>
                </div>
              </article>
            {/each}
          {/if}
        </Card.Content>
      </Card.Root>
    {/each}
  </section>
</div>

<Dialog.Root bind:open={addOpen} shallowRouting={false}>
  <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>Add food</Dialog.Title>
      <Dialog.Description
        >Choose a saved food or enter nutrition for a one-off item.</Dialog.Description
      >
    </Dialog.Header>
    {#if data.commonEntries.length > 0 && !$entryData.source_id && $entryData.source_type !== "manual"}
      <section
        aria-labelledby="frequently-logged-heading"
        class="bg-muted/35 space-y-3 rounded-lg border p-3"
        data-frequently-logged
      >
        <div class="flex items-start gap-2">
          <Repeat2 class="text-primary mt-0.5 size-4 shrink-0" />
          <div>
            <h3 id="frequently-logged-heading" class="text-sm font-semibold">Frequently logged</h3>
            <p class="text-muted-foreground text-xs">
              Select a usual amount to review it before adding.
            </p>
          </div>
        </div>
        <div class="grid gap-2 sm:grid-cols-2">
          {#each data.commonEntries as commonEntry (commonEntryKey(commonEntry))}
            <button
              type="button"
              class="bg-background hover:bg-accent focus-visible:ring-ring flex min-w-0 items-center justify-between gap-2 rounded-md border px-3 py-2 text-left transition-colors focus-visible:ring-2 focus-visible:outline-none"
              aria-label={`Use frequently logged ${commonEntryName(commonEntry)}, ${formatNutrition(commonEntry.quantity)} ${commonEntry.unit}`}
              onclick={() => startCommonAdd(commonEntry)}
            >
              <span class="min-w-0">
                <span class="block truncate text-sm font-medium"
                  >{commonEntryName(commonEntry)}</span
                >
                <span class="text-muted-foreground block truncate text-xs">
                  {formatNutrition(commonEntry.quantity)}
                  {commonEntry.unit} · {formatNutrition(commonEntry.calories)} kcal · {commonEntry.use_count}
                  {commonEntry.use_count === 1 ? "log" : "logs"}
                </span>
              </span>
              <Badge variant="secondary" class="shrink-0 text-[10px]">
                {sourceTypeLabels[commonEntry.source_type]}
              </Badge>
            </button>
          {/each}
        </div>
      </section>
    {/if}
    {#if actionError}
      <Alert.Root variant="destructive">
        <CircleAlert />
        <Alert.Title>Unable to add food</Alert.Title>
        <Alert.Description>{actionError}</Alert.Description>
      </Alert.Root>
    {/if}
    <form method="POST" action="?/saveEntry" use:entryEnhance class="space-y-5">
      <NutritionEntryEditor
        form={entryForm}
        bind:entry={$entryData}
        recipes={data.catalog.recipes}
        products={data.catalog.products}
        ingredients={data.catalog.ingredients}
      />
      <Dialog.Footer class="gap-2 [&>button]:h-11 [&>button]:w-full sm:[&>button]:w-auto">
        <Button type="button" variant="outline" onclick={() => (addOpen = false)}>Cancel</Button>
        <Button type="submit" disabled={!entryComplete || $entrySubmitting}>
          {#if $entrySubmitting}<LoaderCircle class="animate-spin" />{/if} Add to diary
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

<Dialog.Root bind:open={editOpen} shallowRouting={false}>
  <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>Edit diary entry</Dialog.Title>
      <Dialog.Description
        >Moving a meal or changing the food is recalculated safely by the server.</Dialog.Description
      >
    </Dialog.Header>
    {#if actionError}
      <Alert.Root variant="destructive">
        <CircleAlert />
        <Alert.Title>Unable to update entry</Alert.Title>
        <Alert.Description>{actionError}</Alert.Description>
      </Alert.Root>
    {/if}
    {#if editReplacing}
      <form method="POST" action="?/saveEntry" use:entryEnhance class="space-y-5">
        <NutritionEntryEditor
          form={entryForm}
          bind:entry={$entryData}
          recipes={data.catalog.recipes}
          products={data.catalog.products}
          ingredients={data.catalog.ingredients}
        />
        <Dialog.Footer
          class="flex-col gap-2 sm:flex-row [&>button]:h-11 [&>button]:w-full sm:[&>button]:w-auto"
        >
          <Button type="button" variant="outline" onclick={() => (editOpen = false)}>Cancel</Button>
          <Button type="button" variant="secondary" onclick={toggleEditMode}>
            Keep original food
          </Button>
          <Button type="submit" disabled={!editComplete || $entrySubmitting}>
            {#if $entrySubmitting}<LoaderCircle class="animate-spin" />{/if} Save changes
          </Button>
        </Dialog.Footer>
      </form>
    {:else}
      <form method="POST" action="?/move" use:moveEnhance class="space-y-5">
        <div class="grid gap-4 sm:grid-cols-2">
          <Field form={moveForm} name="log_date">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Date</Label>
                  <Input {...props} type="date" bind:value={$moveData.log_date} />
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
          <Field form={moveForm} name="meal_type">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Meal</Label>
                  <select
                    {...props}
                    bind:value={$moveData.meal_type}
                    class="border-input bg-background h-10 w-full rounded-md border px-3 text-sm"
                  >
                    {#each mealTypes as mealType}
                      <option value={mealType}>{mealTypeLabels[mealType]}</option>
                    {/each}
                  </select>
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
          <div class="sm:col-span-2">
            <Field form={moveForm} name="note">
              <div class="space-y-2">
                <Control>
                  {#snippet children({ props })}
                    <Label>Note</Label>
                    <textarea
                      {...props}
                      bind:value={$moveData.note}
                      rows="3"
                      class="border-input bg-background focus-visible:ring-ring w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
                    ></textarea>
                  {/snippet}
                </Control>
                <FieldErrors />
              </div>
            </Field>
          </div>
        </div>
        <Dialog.Footer
          class="flex-col gap-2 sm:flex-row [&>button]:h-11 [&>button]:w-full sm:[&>button]:w-auto"
        >
          <Button type="button" variant="outline" onclick={() => (editOpen = false)}>Cancel</Button>
          <Button type="button" variant="secondary" onclick={toggleEditMode}>
            Change food or amount
          </Button>
          <Button type="submit" disabled={$moveSubmitting}>
            {#if $moveSubmitting}<LoaderCircle class="animate-spin" />{/if} Save changes
          </Button>
        </Dialog.Footer>
      </form>
    {/if}
  </Dialog.Content>
</Dialog.Root>

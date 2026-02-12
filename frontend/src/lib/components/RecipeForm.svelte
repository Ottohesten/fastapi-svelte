<script lang="ts">
  import { page } from "$app/stores";
  import { browser } from "$app/environment";
  import { onMount, untrack } from "svelte";
  import SuperDebug, { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import { RecipeSchema } from "$lib/schemas/schemas";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import InstructionsEditor from "$lib/components/InstructionsEditor.svelte";
  import * as Select from "$lib/components/ui/select/index.js";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Combobox } from "$lib/components/ui/combobox";
  import { Field, Control, Label as SnapLabel, FieldErrors } from "formsnap";

  interface Props {
    data: any;
    pageTitle: string;
    pageDescription: string;
    submitButtonText: string;
    submitButtonColor?: "blue" | "emerald";
    onSubmit?: () => void;
  }

  let {
    data,
    pageTitle,
    pageDescription,
    submitButtonText,
    submitButtonColor = "blue",
    onSubmit
  }: Props = $props();

  const form = superForm(
    untrack(() => data.form),
    {
      validators: zodClient(RecipeSchema),
      dataType: "json",
      onUpdated({ form: f }) {
        if (f.valid && browser) {
          localStorage.removeItem(`recipe-snapshot-${$page.url.pathname}`);
        }
      },
      onResult({ result }) {
        if (result.type === "redirect") {
          if (browser) {
            localStorage.removeItem(`recipe-snapshot-${$page.url.pathname}`);
          }
        }
      }
    }
  );

  const { form: formData, errors, message, constraints, enhance, reset } = form;

  // Derived state for available ingredients
  let availableIngredients = $derived(
    data.ingredients.filter(
      (i: any) => !$formData.ingredients.some((selected: any) => selected.id === i.id)
    )
  );

  // Function to clear form and localStorage
  function clearForm() {
    if (confirm("Are you sure you want to clear the form? This action cannot be undone.")) {
      // Clear localStorage
      if (browser) {
        localStorage.removeItem(`recipe-snapshot-${$page.url.pathname}`);
      }

      // Reset the form
      reset();
    }
  }

  onMount(() => {
    if (browser) {
      const stored = localStorage.getItem(`recipe-snapshot-${$page.url.pathname}`);
      if (stored) {
        try {
          const snapshot = JSON.parse(stored);
          $formData = { ...$formData, ...snapshot };
        } catch (e) {
          console.error("Failed to restore form", e);
        }
      }
    }
  });

  $effect(() => {
    if (browser && $formData) {
      localStorage.setItem(`recipe-snapshot-${$page.url.pathname}`, JSON.stringify($formData));
    }
  });

  // Ingredient dialog state
  let selectedIngredientId = $state<string>("");
  let ingredientAmount = $state<number>(1.0);
  let ingredientUnit = $state<string>("g");
  let open = $state(false);

  // Edit ingredient dialog state
  let editingIngredientId = $state<string | null>(null);
  let editAmount = $state<number>(1.0);
  let editUnit = $state<string>("g");
  let editOpen = $state(false);

  const units = [
    { value: "g", label: "grams (g)" },
    { value: "kg", label: "kilograms (kg)" },
    { value: "ml", label: "milliliters (ml)" },
    { value: "L", label: "liters (L)" },
    { value: "pcs", label: "pieces (pcs)" }
  ];

  let selectedUnitLabel = $derived(
    units.find((u) => u.value === ingredientUnit)?.label ?? "Select a unit"
  );

  // Color variations for submit button
  const colorClasses = {
    blue: "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:ring-blue-500",
    emerald:
      "bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 focus:ring-emerald-500"
  };

  let previewUrl = $state("");

  onMount(() => {
    if (data.recipe?.image) {
      previewUrl = data.recipe.image;
    }
  });
</script>

<SuperDebug data={$formData} />

<div
  class="min-h-screen bg-linear-to-br from-slate-50 to-blue-50 py-8 dark:from-gray-950 dark:to-gray-900"
>
  <div class="container mx-auto max-w-7xl px-4">
    <!-- Page Header -->
    <div class="mb-8 flex items-start justify-between">
      <div>
        <h1 class="mb-2 text-3xl font-bold text-gray-900 dark:text-gray-100">{pageTitle}</h1>
        <p class="text-gray-600 dark:text-gray-300">{pageDescription}</p>
      </div>
      <button
        onclick={clearForm}
        class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-red-50 hover:text-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-red-900/20 dark:hover:text-red-400"
        type="button"
      >
        Clear Form
      </button>
    </div>

    {#if $message}
      <div
        class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900/50 dark:bg-green-900/20"
      >
        <h3 class="text-center text-lg font-medium text-green-800 dark:text-green-300">
          {$message}
        </h3>
      </div>
    {/if}

    <div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <!-- Main Form -->
      <div class="lg:col-span-2">
        <div class="surface-2 rounded-xl p-6">
          <form method="POST" action="" enctype="multipart/form-data" use:enhance class="space-y-6">
            <input type="hidden" name="clearImage" value={$formData.clearImage} />
            <!-- Image Upload -->
            <Field {form} name="image">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <SnapLabel>Recipe Image</SnapLabel>

                    {#if previewUrl}
                      <div
                        class="relative mb-4 aspect-video w-full overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <img
                          src={previewUrl}
                          alt="Recipe preview"
                          class="h-full w-full object-cover"
                        />
                        <button
                          type="button"
                          aria-label="Remove image"
                          class="absolute top-2 right-2 rounded-full bg-red-600 p-1.5 text-white shadow-sm hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
                          onclick={() => {
                            previewUrl = "";
                            $formData.image = null;
                            $formData.clearImage = true;
                            // If we have a file input, reset it
                            const input = document.getElementById(props.id) as HTMLInputElement;
                            if (input) input.value = "";
                          }}
                        >
                          <svg
                            class="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    {/if}

                    <div class="flex items-center gap-4">
                      <Input
                        {...props}
                        type="file"
                        accept="image/*"
                        class="cursor-pointer file:cursor-pointer"
                        onchange={(e) => {
                          const file = e.currentTarget.files?.[0];
                          if (file) {
                            $formData.image = file;
                            $formData.clearImage = false;
                            previewUrl = URL.createObjectURL(file);
                          }
                        }}
                      />
                    </div>
                  </div>
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>

            <!-- Title Field -->
            <Field {form} name="title">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <SnapLabel>Recipe Title <span class="text-red-500">*</span></SnapLabel>
                    <input
                      {...props}
                      {...$constraints.title}
                      class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
                      type="text"
                      placeholder="Enter a delicious recipe name..."
                      bind:value={$formData.title}
                    />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>

            <!-- Servings -->
            <Field {form} name="servings">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <SnapLabel>Servings <span class="text-red-500">*</span></SnapLabel>
                    <input
                      {...props}
                      {...$constraints.servings}
                      class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
                      type="number"
                      min="1"
                      placeholder="Enter number of servings"
                      bind:value={$formData.servings}
                    />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>

            <!-- Instructions Field -->
            <Field {form} name="instructions">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <SnapLabel>Cooking Instructions <span class="text-red-500">*</span></SnapLabel>
                    <div
                      class="rounded-lg border border-gray-300 bg-white shadow-sm transition-colors focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40 dark:focus-within:border-blue-400 dark:focus-within:ring-blue-400/20"
                    >
                      <InstructionsEditor bind:value={$formData.instructions} />
                    </div>
                    <input {...props} type="hidden" bind:value={$formData.instructions} />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>

            <!-- Add Ingredient Section -->
            <div class="space-y-2">
              <Label for="add-ingredient-trigger">Ingredients</Label>
              <Dialog.Root bind:open>
                <Dialog.Trigger
                  id="add-ingredient-trigger"
                  onclick={(event) => {
                    event.preventDefault();
                    open = true;
                  }}
                  class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                    />
                  </svg>
                  Add Ingredient
                </Dialog.Trigger>
                <Dialog.Content class="sm:max-w-md">
                  <Dialog.Header>
                    <Dialog.Title class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Add Ingredient
                    </Dialog.Title>
                    <Dialog.Description class="text-sm text-gray-600 dark:text-gray-300">
                      Select an ingredient to add to your recipe.
                    </Dialog.Description>
                  </Dialog.Header>
                  <div class="space-y-4">
                    <div>
                      <Label for="ingredient-select" class="mb-2">Choose Ingredient</Label>
                      <Combobox
                        items={availableIngredients.map((i: any) => ({
                          label: i.title,
                          value: i.id
                        }))}
                        bind:value={selectedIngredientId}
                        placeholder="Select an ingredient..."
                        searchPlaceholder="Type to filter ingredients..."
                        ariaLabel="Ingredient"
                        buttonClass="w-full justify-between"
                        popoverClass="w-full min-w-[var(--radix-popover-trigger-width)]"
                        class="w-full"
                      />
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                      <div>
                        <Label for="ingredient-amount" class="mb-2">Amount</Label>
                        <input
                          id="ingredient-amount"
                          type="number"
                          min="0.1"
                          step="0.1"
                          class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
                          bind:value={ingredientAmount}
                          placeholder="1"
                        />
                      </div>
                      <div>
                        <Label for="ingredient-unit" class="mb-2">Unit</Label>
                        <Select.Root type="single" bind:value={ingredientUnit}>
                          <Select.Trigger id="ingredient-unit" class="h-11 w-full justify-between">
                            {selectedUnitLabel}
                          </Select.Trigger>
                          <Select.Content>
                            {#each units as unit}
                              <Select.Item value={unit.value} label={unit.label}>
                                {unit.label}
                              </Select.Item>
                            {/each}
                          </Select.Content>
                        </Select.Root>
                      </div>
                    </div>
                  </div>
                  <Dialog.Footer class="flex gap-3">
                    <button
                      type="button"
                      class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
                      onclick={() => {
                        // Reset form when canceling
                        selectedIngredientId = "";
                        ingredientAmount = 1.0;
                        ingredientUnit = "g";
                        open = false;
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      class="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-300"
                      disabled={!selectedIngredientId ||
                        !ingredientAmount ||
                        ingredientAmount < 0.1}
                      onclick={(event) => {
                        event.preventDefault();
                        const ingredient = data.ingredients.find(
                          (i: any) => i.id === selectedIngredientId
                        );
                        if (ingredient) {
                          // Create the ingredient link object that matches your schema
                          const ingredientLink = {
                            id: ingredient.id,
                            title: ingredient.title,
                            calories: ingredient.calories,
                            amount: ingredientAmount,
                            unit: ingredientUnit as "g" | "kg" | "ml" | "L" | "pcs"
                          };
                          $formData.ingredients = $formData.ingredients.concat({
                            id: ingredientLink.id,
                            title: ingredientLink.title, // Include title for display
                            amount: ingredientLink.amount,
                            unit: ingredientLink.unit
                          });
                          // Reset form
                          selectedIngredientId = "";
                          ingredientAmount = 1.0;
                          ingredientUnit = "g";
                          open = false;
                        } else {
                          alert("Ingredient not found");
                        }
                      }}
                    >
                      Add Ingredient
                    </button>
                  </Dialog.Footer>
                </Dialog.Content>
              </Dialog.Root>
            </div>

            <!-- Submit Button -->
            <div class="border-t border-gray-200 pt-4 dark:border-gray-800">
              <button
                class="w-full rounded-lg {colorClasses[
                  submitButtonColor
                ]} px-6 py-3 text-base font-semibold text-white shadow-lg transition-all hover:shadow-xl focus:ring-2 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-gray-900"
                type="submit"
                onclick={() => {
                  onSubmit?.();
                }}
              >
                {submitButtonText}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Ingredients Sidebar -->
      <div class="lg:col-span-1">
        <div class="surface-2 sticky top-8 rounded-xl p-6">
          <div class="mb-4 flex items-center gap-2">
            <svg
              class="h-5 w-5 text-green-600"
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
            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recipe Ingredients
            </h2>
          </div>

          {#if $formData.ingredients.length === 0}
            <div class="py-8 text-center">
              <div
                class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800"
              >
                <svg
                  class="h-8 w-8 text-gray-400 dark:text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400">No ingredients added yet</p>
              <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
                Click "Add Ingredient" to get started
              </p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each $formData.ingredients as ingredient, index}
                <div
                  class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900/40 dark:hover:bg-gray-900/60"
                >
                  <div class="flex items-center gap-3">
                    <span
                      class="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-600 dark:bg-blue-900/30 dark:text-blue-300"
                    >
                      {index + 1}
                    </span>
                    <div class="flex flex-col">
                      <span class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {ingredient.title || "Unknown Ingredient"}
                      </span>
                      <span class="text-xs text-gray-500 dark:text-gray-400">
                        {ingredient.amount || 0}
                        {ingredient.unit || "units"}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      type="button"
                      aria-label="Edit ingredient"
                      onclick={() => {
                        editingIngredientId = ingredient.id;
                        editAmount = ingredient.amount;
                        editUnit = ingredient.unit;
                        editOpen = true;
                      }}
                      class="rounded-lg p-1.5 text-blue-500 transition-colors hover:bg-blue-50 hover:text-blue-700 dark:hover:bg-blue-900/20"
                      title="Edit ingredient"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      aria-label="Remove ingredient"
                      onclick={() => {
                        $formData.ingredients = $formData.ingredients.filter(
                          (i: any) => i.id !== ingredient.id
                        );
                      }}
                      class="rounded-lg p-1.5 text-red-500 transition-colors hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-900/20"
                      title="Remove ingredient"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
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

<!-- Edit Ingredient Dialog -->
<Dialog.Root bind:open={editOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title class="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Edit Ingredient
      </Dialog.Title>
      <Dialog.Description class="text-sm text-gray-600 dark:text-gray-300">
        Update the amount and unit for this ingredient.
      </Dialog.Description>
    </Dialog.Header>
    <div class="space-y-4">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <Label for="edit-ingredient-amount" class="mb-2">Amount</Label>
          <input
            id="edit-ingredient-amount"
            type="number"
            min="0.1"
            step="0.1"
            class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-400/20"
            bind:value={editAmount}
            placeholder="1"
          />
        </div>
        <div>
          <Label for="edit-ingredient-unit" class="mb-2">Unit</Label>
          <Select.Root type="single" bind:value={editUnit}>
            <Select.Trigger id="edit-ingredient-unit" class="h-11 w-full justify-between">
              {units.find((u) => u.value === editUnit)?.label ?? "Select a unit"}
            </Select.Trigger>
            <Select.Content>
              {#each units as unit}
                <Select.Item value={unit.value} label={unit.label}>
                  {unit.label}
                </Select.Item>
              {/each}
            </Select.Content>
          </Select.Root>
        </div>
      </div>
    </div>
    <Dialog.Footer class="flex gap-3">
      <button
        type="button"
        class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
        onclick={() => {
          editingIngredientId = null;
          editAmount = 1.0;
          editUnit = "g";
          editOpen = false;
        }}
      >
        Cancel
      </button>
      <button
        type="button"
        class="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-300"
        disabled={!editAmount || editAmount < 0.1}
        onclick={() => {
          if (editingIngredientId) {
            $formData.ingredients = $formData.ingredients.map((ing: any) => {
              if (ing.id === editingIngredientId) {
                return {
                  ...ing,
                  amount: editAmount,
                  unit: editUnit as "g" | "kg" | "ml" | "L" | "pcs"
                };
              }
              return ing;
            });
            editingIngredientId = null;
            editAmount = 1.0;
            editUnit = "g";
            editOpen = false;
          }
        }}
      >
        Save Changes
      </button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

<style>
  /* Custom styles for enhanced visual appeal */
  :global(.tiptap-container .tiptap) {
    min-height: 200px;
    padding: 1rem;
    border-radius: 0.5rem;
    background: white;
  }

  :global(.instructions-editor .control-group) {
    margin-bottom: 0;
    padding: 0.75rem;
    background: #f8fafc;
    border-top-left-radius: 0.5rem;
    border-top-right-radius: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
  }
</style>

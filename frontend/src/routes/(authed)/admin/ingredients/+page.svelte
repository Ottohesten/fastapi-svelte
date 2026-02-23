<script lang="ts">
  let { data } = $props();
  import DataTable from "$lib/components/ui/data-table.svelte";
  import Button, { buttonVariants } from "$lib/components/ui/button/button.svelte";
  import { enhance } from "$app/forms";
  import { createColumns } from "./columns.js";
  import { invalidateAll } from "$app/navigation";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import { Input } from "$lib/components/ui/input";
  import { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import { IngredientSchema, IngredientUpdateSchema } from "$lib/schemas/schemas.js";
  import { Field, Control, Label, FieldErrors } from "formsnap";

  let open = $state(false);

  const form = superForm(
    untrack(() => data.ingredientCreateForm),
    {
      id: "ingredientCreateForm",
      validators: zodClient(IngredientSchema),
      resetForm: true,
      onUpdated: ({ form }) => {
        if (form.valid && form.message) {
          open = false;
        }
      }
    }
  );

  const updateForm = superForm(
    untrack(() => data.ingredientUpdateForm),
    {
      id: "ingredientUpdateForm",
      validators: zodClient(IngredientUpdateSchema),
      resetForm: false,
      onUpdated: ({ form }) => {
        if (form.valid && form.message) {
          console.log("Update form valid:", form.message);
        }
      }
    }
  );

  const { form: formData, enhance: formEnhance, errors, message } = form;
  const { message: updateMessage } = updateForm;

  $effect(() => {
    if ($message) {
      const timer = setTimeout(() => {
        $message = undefined;
      }, 3000);
      return () => clearTimeout(timer);
    }
  });

  $effect(() => {
    if ($updateMessage) {
      const timer = setTimeout(() => {
        $updateMessage = undefined;
      }, 3000);
      return () => clearTimeout(timer);
    }
  });

  const columns = createColumns(updateForm);
</script>

<div class="mx-auto max-w-7xl">
  <div class="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-2xl font-bold">Ingredients</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-300">
        Manage ingredients and their nutritional information
      </p>
    </div>

    {#if $message && $message.includes("successfully")}
      <div
        out:fade
        class="rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-900/50 dark:bg-green-900/20"
      >
        <p class="text-sm text-green-800 dark:text-green-300">{$message}</p>
      </div>
    {/if}

    {#if $updateMessage && $updateMessage.includes("successfully")}
      <div
        out:fade
        class="rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-900/50 dark:bg-green-900/20"
      >
        <p class="text-sm text-green-800 dark:text-green-300">{$updateMessage}</p>
      </div>
    {/if}

    <Dialog.Root bind:open>
      <Dialog.Trigger class={buttonVariants()}>Add Ingredient</Dialog.Trigger>
      <Dialog.Content class="sm:max-w-[425px]">
        <Dialog.Header>
          <Dialog.Title>Add New Ingredient</Dialog.Title>
          <Dialog.Description>Add a new ingredient to the database.</Dialog.Description>
        </Dialog.Header>
        <form method="POST" action="?/create" use:formEnhance class="space-y-4">
          {#if $message && !$message.includes("successfully")}
            <div class="rounded-md border border-red-200 bg-red-50 p-3">
              <p class="text-sm text-red-600">
                {$message}
              </p>
            </div>
          {/if}
          <div class="space-y-4">
            <Field {form} name="title">
              <Control>
                {#snippet children({ props })}
                  <Label>Name</Label>
                  <Input
                    {...props}
                    type="text"
                    bind:value={$formData.title}
                    placeholder="Enter ingredient name"
                    class="mt-2"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
            <Field {form} name="calories">
              <Control>
                {#snippet children({ props })}
                  <Label>Calories (per 100g)</Label>
                  <Input
                    {...props}
                    type="number"
                    bind:value={$formData.calories}
                    placeholder="Enter calories"
                    class="mt-2"
                    min="0"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
            <Field {form} name="carbohydrates">
              <Control>
                {#snippet children({ props })}
                  <Label>Carbohydrates (per 100g)</Label>
                  <Input
                    {...props}
                    type="number"
                    bind:value={$formData.carbohydrates}
                    placeholder="Enter carbohydrates"
                    class="mt-2"
                    min="0"
                    step="0.1"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
            <Field {form} name="fat">
              <Control>
                {#snippet children({ props })}
                  <Label>Fat (per 100g)</Label>
                  <Input
                    {...props}
                    type="number"
                    bind:value={$formData.fat}
                    placeholder="Enter fat"
                    class="mt-2"
                    min="0"
                    step="0.1"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
            <Field {form} name="protein">
              <Control>
                {#snippet children({ props })}
                  <Label>Protein (per 100g)</Label>
                  <Input
                    {...props}
                    type="number"
                    bind:value={$formData.protein}
                    placeholder="Enter protein"
                    class="mt-2"
                    min="0"
                    step="0.1"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
            <Field {form} name="weight_per_piece">
              <Control>
                {#snippet children({ props })}
                  <Label>Weight per piece (g)</Label>
                  <Input
                    {...props}
                    type="number"
                    bind:value={$formData.weight_per_piece}
                    placeholder="Enter weight per piece"
                    class="mt-2"
                    min="1"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>
          </div>
          <Dialog.Footer>
            <Button type="submit">Add Ingredient</Button>
          </Dialog.Footer>
        </form>
      </Dialog.Content>
    </Dialog.Root>
  </div>

  <DataTable
    data={data.ingredients}
    {columns}
    searchColumn="title"
    searchPlaceholder="Filter ingredients..."
  />
</div>

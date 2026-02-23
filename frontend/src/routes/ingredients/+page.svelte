<script lang="ts">
  import Ingredient from "$lib/components/Ingredient.svelte";

  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { superForm, type SuperValidated, type Infer } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import SuperDebug from "sveltekit-superforms";
  import { untrack } from "svelte";
  import { Field, Control, Label, Description, FieldErrors } from "formsnap";
  import { Input } from "$lib/components/ui/input/index.js";
  import { IngredientSchema } from "$lib/schemas/schemas.js";

  let { data } = $props();

  let dialogOpen = $state(false);

  const form = superForm(
    untrack(() => data.ingredientCreateForm),
    {
      validators: zodClient(IngredientSchema),
      resetForm: true,
      onUpdated: ({ form }) => {
        console.log("Form updated:", {
          valid: form.valid,
          message: form.message,
          errors: form.errors
        });
        if (form.valid && form.message) {
          // console.log('Closing dialog...');
          dialogOpen = false;
        }
      }
    }
  );

  const { form: formData, enhance, errors, message } = form;
</script>

<!-- {JSON.stringify(data)} -->

<div class="container mx-auto px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
  <!-- message -->
  {#if $message}
    <div class="mb-4 rounded border border-green-200 bg-green-100 p-4 text-center">
      <p class="text-green-700">{$message}</p>
    </div>
  {/if}
  <div class="mb-6 flex flex-col items-center justify-between sm:flex-row">
    <h1 class="mb-4 text-2xl font-bold sm:mb-0 sm:text-3xl lg:text-4xl">Ingredients:</h1>

    {#if data.authenticatedUser && data.authenticatedUser.is_superuser}
      <Dialog.Root bind:open={dialogOpen}>
        <Dialog.Trigger
          class="bg-primary text-primary-foreground ring-offset-background hover:bg-primary/90 focus-visible:ring-ring inline-flex h-10 w-full items-center justify-center rounded-md px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 sm:w-auto"
        >
          Create Ingredient
        </Dialog.Trigger>
        <Dialog.Content class="sm:max-w-md">
          <Dialog.Header>
            <Dialog.Title>Create New Ingredient</Dialog.Title>
            <Dialog.Description>Add a new ingredient to the database.</Dialog.Description>
          </Dialog.Header>

          <form method="POST" action="?/create" use:enhance class="space-y-4">
            <div class="grid grid-cols-1 gap-2">
              <Field {form} name="title">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700">Title *</Label>
                    <Input
                      {...props}
                      type="text"
                      bind:value={$formData.title}
                      placeholder="Enter ingredient title"
                    />
                  {/snippet}
                </Control>
                <FieldErrors />
              </Field>
              <Field {form} name="calories">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700">Calories *</Label>
                    <Input
                      {...props}
                      type="number"
                      bind:value={$formData.calories}
                      placeholder="Calories per 100g"
                    />
                  {/snippet}
                </Control>
                <Description class="text-sm text-gray-500">Calories per 100g</Description>
                <FieldErrors />
              </Field>
              <Field {form} name="carbohydrates">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700"
                      >Carbohydrates (g) *</Label
                    >
                    <Input
                      {...props}
                      type="number"
                      min="0"
                      step="0.1"
                      bind:value={$formData.carbohydrates}
                      placeholder="Carbohydrates per 100g"
                    />
                  {/snippet}
                </Control>
                <Description class="text-sm text-gray-500">Carbohydrates per 100g</Description>
                <FieldErrors />
              </Field>
              <Field {form} name="fat">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700">Fat (g) *</Label>
                    <Input
                      {...props}
                      type="number"
                      min="0"
                      step="0.1"
                      bind:value={$formData.fat}
                      placeholder="Fat per 100g"
                    />
                  {/snippet}
                </Control>
                <Description class="text-sm text-gray-500">Fat per 100g</Description>
                <FieldErrors />
              </Field>
              <Field {form} name="protein">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700">Protein (g) *</Label
                    >
                    <Input
                      {...props}
                      type="number"
                      min="0"
                      step="0.1"
                      bind:value={$formData.protein}
                      placeholder="Protein per 100g"
                    />
                  {/snippet}
                </Control>
                <Description class="text-sm text-gray-500">Protein per 100g</Description>
                <FieldErrors />
              </Field>
              <Field {form} name="weight_per_piece">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium text-gray-700"
                      >Weight Per Piece (g) *</Label
                    >
                    <Input
                      {...props}
                      type="number"
                      min="1"
                      bind:value={$formData.weight_per_piece}
                      placeholder="Weight per piece in grams"
                    />
                  {/snippet}
                </Control>
                <Description class="text-sm text-gray-500">Used when unit is pcs</Description>
                <FieldErrors />
              </Field>
            </div>

            <Dialog.Footer class="mt-6">
              <Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
                Cancel
              </Button>
              <Button type="submit">Create Ingredient</Button>
            </Dialog.Footer>
          </form>
        </Dialog.Content>
      </Dialog.Root>
    {/if}
  </div>

  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
    {#each data.ingredients as ingredient}
      <Ingredient user={data.authenticatedUser} {ingredient} />
    {/each}
  </div>
</div>

<script lang="ts">
  let { data } = $props();
  import DataTable from "$lib/components/ui/data-table.svelte";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import Button, { buttonVariants } from "$lib/components/ui/button/button.svelte";
  import { enhance } from "$app/forms";
  import { createColumns } from "./columns.js";
  import { invalidateAll } from "$app/navigation";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Input } from "$lib/components/ui/input";
  import { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import { IngredientSchema, IngredientUpdateSchema } from "$lib/schemas/schemas.js";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { CircleCheck, LoaderCircle, ScanLine, TriangleAlert } from "@lucide/svelte";
  import type { OpenFoodFactsProductPublic } from "$lib/client";
  import BarcodeScanner from "./BarcodeScanner.svelte";

  let open = $state(false);
  let scanMode = $state(false);
  let lookupLoading = $state(false);
  let lookupError = $state("");
  let importedProduct = $state<OpenFoodFactsProductPublic | null>(null);

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

  $effect(() => {
    if (!open) {
      scanMode = false;
      lookupLoading = false;
      lookupError = "";
      importedProduct = null;
    }
  });

  const columns = createColumns(updateForm);

  function startScanning() {
    lookupError = "";
    importedProduct = null;
    scanMode = true;
  }

  async function lookupBarcode(barcode: string) {
    lookupLoading = true;
    lookupError = "";

    try {
      const response = await fetch(`/admin/ingredients/barcode/${encodeURIComponent(barcode)}`);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Product lookup failed");
      }

      const product = result as OpenFoodFactsProductPublic;
      if (product.existing_ingredient_id) {
        throw new Error(`${product.title} is already in the ingredient database.`);
      }

      $formData.title = product.title;
      $formData.calories = product.calories;
      $formData.carbohydrates = product.carbohydrates;
      $formData.fat = product.fat;
      $formData.protein = product.protein;
      $formData.weight_per_piece = product.weight_per_piece;
      $formData.barcode = product.barcode;
      importedProduct = product;
    } catch (error) {
      lookupError = error instanceof Error ? error.message : "Product lookup failed";
    } finally {
      lookupLoading = false;
      scanMode = false;
    }
  }
</script>

<div class="mx-auto max-w-7xl space-y-6">
  <AdminPageHeader
    title="Ingredients"
    description="Manage ingredients and their nutritional information."
  >
    {#snippet action()}
      <Dialog.Root bind:open>
        <Dialog.Trigger class={`${buttonVariants()} w-full sm:w-auto`}>
          Add Ingredient
        </Dialog.Trigger>
        <Dialog.Content class="max-h-[90vh] overflow-y-auto sm:max-w-[540px]">
          <Dialog.Header>
            <Dialog.Title>{scanMode ? "Scan a barcode" : "Add New Ingredient"}</Dialog.Title>
            <Dialog.Description>
              {scanMode
                ? "Use your phone camera to find the product in Open Food Facts."
                : "Review the nutritional values before adding the ingredient."}
            </Dialog.Description>
          </Dialog.Header>

          {#if scanMode}
            {#if lookupLoading}
              <div class="grid min-h-64 place-items-center">
                <div class="text-muted-foreground flex flex-col items-center gap-3 text-sm">
                  <LoaderCircle class="size-8 animate-spin" />
                  Looking up product…
                </div>
              </div>
            {:else}
              <BarcodeScanner onDetected={lookupBarcode} />
            {/if}
            <Dialog.Footer class="[&>button]:w-full sm:[&>button]:w-auto">
              <Button type="button" variant="outline" onclick={() => (scanMode = false)}>
                Cancel
              </Button>
            </Dialog.Footer>
          {:else}
            <form method="POST" action="?/create" use:formEnhance class="space-y-4">
              <input type="hidden" name="barcode" value={$formData.barcode ?? ""} />

              <Button type="button" variant="outline" class="w-full" onclick={startScanning}>
                <ScanLine class="size-5" />
                Scan product barcode
              </Button>

              {#if lookupError}
                <Alert.Root variant="destructive">
                  <TriangleAlert />
                  <Alert.Title>Product lookup failed</Alert.Title>
                  <Alert.Description>{lookupError}</Alert.Description>
                </Alert.Root>
              {/if}

              {#if importedProduct}
                <div class="bg-muted/40 flex gap-3 rounded-lg border p-3">
                  {#if importedProduct.image_url}
                    <img
                      src={importedProduct.image_url}
                      alt={importedProduct.title}
                      class="size-16 shrink-0 rounded-md bg-white object-contain"
                    />
                  {/if}
                  <div class="min-w-0 text-sm">
                    <p class="font-medium">{importedProduct.title}</p>
                    {#if importedProduct.brand}
                      <p class="text-muted-foreground">{importedProduct.brand}</p>
                    {/if}
                    <p class="text-muted-foreground font-mono text-xs">{importedProduct.barcode}</p>
                    <a
                      class="text-primary text-xs underline-offset-4 hover:underline"
                      href={`https://world.openfoodfacts.org/product/${importedProduct.barcode}`}
                      target="_blank"
                      rel="noreferrer">Open Food Facts source</a
                    >
                  </div>
                </div>

                {#if importedProduct.missing_nutrients.length || importedProduct.nutrition_basis !== "100g"}
                  <Alert.Root class="border-accent bg-accent/50">
                    <TriangleAlert />
                    <Alert.Title>Check the product label</Alert.Title>
                    <Alert.Description>
                      {#if importedProduct.missing_nutrients.length}
                        <p>
                          Missing values were set to zero: {importedProduct.missing_nutrients
                            .map((name) => name.replace("energy-kcal", "calories"))
                            .join(", ")}.
                        </p>
                      {/if}
                      {#if importedProduct.nutrition_basis !== "100g"}
                        <p>
                          Open Food Facts reports these values per {importedProduct.nutrition_basis}.
                        </p>
                      {/if}
                      <p>Please check the label before saving.</p>
                    </Alert.Description>
                  </Alert.Root>
                {/if}
              {/if}

              {#if $message && !$message.includes("successfully")}
                <Alert.Root variant="destructive">
                  <TriangleAlert />
                  <Alert.Title>Unable to add ingredient</Alert.Title>
                  <Alert.Description>{$message}</Alert.Description>
                </Alert.Root>
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
              <Dialog.Footer class="[&>button]:w-full sm:[&>button]:w-auto">
                <Button type="submit">Add Ingredient</Button>
              </Dialog.Footer>
            </form>
          {/if}
        </Dialog.Content>
      </Dialog.Root>
    {/snippet}
  </AdminPageHeader>

  <div class="space-y-3">
    {#if $message && $message.includes("successfully")}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>Ingredient added</Alert.Title>
          <Alert.Description>{$message}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}

    {#if $updateMessage && $updateMessage.includes("successfully")}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>Ingredient updated</Alert.Title>
          <Alert.Description>{$updateMessage}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}
  </div>

  <DataTable
    data={data.ingredients}
    {columns}
    searchColumn="title"
    searchPlaceholder="Filter ingredients..."
  />
</div>

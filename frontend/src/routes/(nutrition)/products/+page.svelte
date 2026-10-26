<script lang="ts">
  import { applyAction, enhance } from "$app/forms";
  import type { SubmitFunction } from "@sveltejs/kit";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { untrack } from "svelte";
  import { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import {
    Barcode,
    CircleAlert,
    CircleCheck,
    LoaderCircle,
    Package,
    Pencil,
    Plus,
    ScanLine,
    Search,
    Trash2
  } from "@lucide/svelte";
  import type {
    ProductBarcodePreviewPublic,
    ProductNutritionBasis,
    ProductPublic
  } from "$lib/client";
  import BarcodeScannerDialog from "$lib/components/BarcodeScannerDialog.svelte";
  import * as Alert from "$lib/components/ui/alert";
  import { Button, buttonVariants } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Input } from "$lib/components/ui/input";
  import { formatNutrition } from "$lib/nutrition/helpers";
  import { nutritionBasisLabels, nutritionBases } from "$lib/nutrition/types";
  import {
    emptyProductForm,
    ProductFormSchema,
    type ProductFormData
  } from "$lib/schemas/nutrition";
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();
  let productOpen = $state(false);
  let scanOpen = $state(false);
  let lookupLoading = $state(false);
  let actionError = $state("");
  let successMessage = $state("");
  let lookupError = $state("");
  let barcodePreview = $state<ProductBarcodePreviewPublic | null>(null);
  let returnToProductFormAfterScan = $state(false);

  const productForm = superForm(
    untrack(() => data.productForm),
    {
      id: "productForm",
      validators: zodClient(ProductFormSchema),
      resetForm: false,
      onSubmit: () => {
        actionError = "";
        successMessage = "";
      },
      onUpdated: ({ form }) => {
        if (typeof form.message === "string") {
          if (form.valid) {
            productOpen = false;
            barcodePreview = null;
            lookupError = "";
            successMessage = form.message;
          } else {
            actionError = form.message;
          }
        }
      }
    }
  );

  const { form: productData, enhance: productEnhance, submitting } = productForm;

  const editing = $derived($productData.id.length > 0);

  $effect(() => {
    if (!scanOpen && returnToProductFormAfterScan && !lookupLoading) {
      returnToProductFormAfterScan = false;
      productOpen = true;
    }
  });

  function productFormData(saved: ProductPublic): ProductFormData {
    return {
      id: saved.id,
      title: saved.title,
      brand: saved.brand ?? "",
      barcode: saved.barcode ?? "",
      image_url: saved.image_url ?? "",
      nutrition_basis: saved.nutrition_basis ?? "per_100g",
      calories: saved.calories,
      carbohydrates: saved.carbohydrates ?? null,
      fat: saved.fat ?? null,
      protein: saved.protein ?? null,
      serving_size: saved.serving_size ?? null,
      serving_size_unit: saved.serving_size_unit ?? "g",
      package_size: saved.package_size ?? null,
      package_size_unit: saved.package_size_unit ?? "g"
    };
  }

  function previewFormData(
    preview: ProductBarcodePreviewPublic,
    fallbackBarcode: string
  ): ProductFormData {
    return {
      id: "",
      title: preview.title,
      brand: preview.brand ?? "",
      barcode: preview.barcode || fallbackBarcode,
      image_url: preview.image_url ?? "",
      nutrition_basis: preview.nutrition_basis,
      calories: preview.calories ?? null,
      carbohydrates: preview.carbohydrates ?? null,
      fat: preview.fat ?? null,
      protein: preview.protein ?? null,
      serving_size: preview.serving_size ?? null,
      serving_size_unit: preview.serving_size_unit ?? "g",
      package_size: preview.package_size ?? null,
      package_size_unit: preview.package_size_unit ?? "g"
    };
  }

  function editProduct(saved: ProductPublic) {
    actionError = "";
    productForm.reset({ data: productFormData(saved) });
    barcodePreview = null;
    lookupError = "";
    productOpen = true;
  }

  function addProduct() {
    actionError = "";
    productForm.reset({ data: emptyProductForm() });
    barcodePreview = null;
    lookupError = "";
    productOpen = true;
  }

  function openBarcodeScanner(returnToProductForm = false) {
    lookupError = "";
    returnToProductFormAfterScan = returnToProductForm;
    if (returnToProductForm) productOpen = false;
    scanOpen = true;
  }

  function actionMessage(result: { data?: Record<string, unknown> }): string {
    const value = result.data?.error;
    return typeof value === "string" ? value : "The request could not be completed.";
  }

  const deleteEnhance: SubmitFunction = () => {
    actionError = "";
    successMessage = "";
    return async ({ result, update }) => {
      if (result.type === "success") {
        successMessage = "Product deleted. Existing diary entries keep their saved nutrition.";
        await update();
        return;
      }
      if (result.type === "failure") {
        actionError = actionMessage(result);
        return;
      }
      await applyAction(result);
    };
  };

  async function lookupBarcode(barcode: string) {
    lookupLoading = true;
    lookupError = "";
    try {
      const response = await fetch(`/products/barcode/${encodeURIComponent(barcode)}`);
      const body = (await response.json()) as ProductBarcodePreviewPublic | { detail?: string };
      if (!response.ok || !("title" in body)) {
        throw new Error("detail" in body && body.detail ? body.detail : "Product lookup failed.");
      }
      if (body.existing_product_id) {
        productForm.reset({
          data: { ...previewFormData(body, barcode), id: body.existing_product_id }
        });
        barcodePreview = null;
        scanOpen = false;
        productOpen = true;
        return;
      }
      barcodePreview = body;
      productForm.reset({ data: previewFormData(body, barcode) });
      scanOpen = false;
      productOpen = true;
    } catch (caught) {
      lookupError = caught instanceof Error ? caught.message : "Product lookup failed.";
      productForm.reset({ data: { ...emptyProductForm(), barcode } });
      barcodePreview = null;
      scanOpen = false;
      productOpen = true;
    } finally {
      lookupLoading = false;
    }
  }

  function nutritionBasis(saved: ProductPublic): ProductNutritionBasis {
    return saved.nutrition_basis ?? "per_100g";
  }

  function defaultLogUnit(saved: ProductPublic): "g" | "ml" | "serving" | "package" {
    const basis = nutritionBasis(saved);
    const basisUnit =
      basis === "per_100g"
        ? "g"
        : basis === "per_100ml"
          ? "ml"
          : basis === "per_serving"
            ? saved.serving_size_unit
            : saved.package_size_unit;
    if (
      basis === "per_package" ||
      (basisUnit && saved.package_size != null && saved.package_size_unit === basisUnit)
    ) {
      return "package";
    }
    if (
      basis === "per_serving" ||
      (basisUnit && saved.serving_size != null && saved.serving_size_unit === basisUnit)
    ) {
      return "serving";
    }
    return basisUnit === "ml" ? "ml" : "g";
  }

  function logHref(saved: ProductPublic): string {
    const params = new URLSearchParams({
      source_type: "product",
      source_id: saved.id,
      quantity: "1",
      unit: defaultLogUnit(saved)
    });
    return `/nutrition?${params}`;
  }
</script>

<svelte:head><title>Products</title></svelte:head>

<Dialog.Root bind:open={productOpen} shallowRouting={false}>
  <div class="container mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-primary text-sm font-semibold tracking-wide uppercase">Personal catalog</p>
        <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">Products</h1>
        <p class="text-muted-foreground mt-2">
          Save packaged foods without turning them into recipes.
        </p>
      </div>
      <div class="grid grid-cols-2 gap-2 sm:flex">
        <Button type="button" variant="outline" class="h-11" onclick={() => openBarcodeScanner()}>
          <ScanLine /> Scan
        </Button>
        <Dialog.Trigger class={buttonVariants({ class: "h-11" })} onclick={addProduct}>
          <Plus /> Add product
        </Dialog.Trigger>
      </div>
    </header>

    {#if actionError || lookupError}
      <Alert.Root variant="destructive">
        <CircleAlert />
        <Alert.Title>Unable to complete the request</Alert.Title>
        <Alert.Description>{actionError || lookupError}</Alert.Description>
      </Alert.Root>
    {:else if successMessage}
      <Alert.Root>
        <CircleCheck />
        <Alert.Title>Done</Alert.Title>
        <Alert.Description>{successMessage}</Alert.Description>
      </Alert.Root>
    {/if}

    <form method="GET" class="flex gap-2">
      <div class="relative min-w-0 flex-1">
        <Search class="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        <Input
          name="query"
          value={data.query}
          class="h-11 pl-9"
          placeholder="Search name, brand, or barcode…"
        />
      </div>
      <Button type="submit" variant="secondary" class="h-11">Search</Button>
      {#if data.query}<Button href="/products" variant="ghost" class="h-11">Clear</Button>{/if}
    </form>

    {#if data.products.length === 0}
      <Card.Root>
        <Card.Content class="grid min-h-64 place-items-center py-10 text-center">
          <div class="max-w-sm">
            <span class="bg-muted mx-auto grid size-12 place-items-center rounded-2xl"
              ><Package /></span
            >
            <h2 class="mt-4 font-semibold">
              {data.query ? "No matching products" : "No products yet"}
            </h2>
            <p class="text-muted-foreground mt-1 text-sm">
              {data.query
                ? "Try a different search."
                : "Scan a barcode or enter the nutrition label manually."}
            </p>
          </div>
        </Card.Content>
      </Card.Root>
    {:else}
      <div class="grid gap-4 md:hidden">
        {#each data.products as saved (saved.id)}
          <Card.Root class="overflow-hidden">
            <Card.Content class="flex gap-4 pt-5">
              {#if saved.image_url}
                <img
                  src={saved.image_url}
                  alt=""
                  class="size-20 shrink-0 rounded-lg bg-white object-contain"
                />
              {:else}
                <span class="bg-muted grid size-20 shrink-0 place-items-center rounded-lg"
                  ><Package /></span
                >
              {/if}
              <div class="min-w-0 flex-1">
                <h2 class="truncate font-semibold">{saved.title}</h2>
                {#if saved.brand}<p class="text-muted-foreground truncate text-sm">
                    {saved.brand}
                  </p>{/if}
                <p class="mt-2 font-medium">
                  {formatNutrition(saved.calories)} kcal
                  <span class="text-muted-foreground text-xs"
                    >{nutritionBasisLabels[nutritionBasis(saved)]}</span
                  >
                </p>
                <p class="text-muted-foreground text-xs">
                  C {formatNutrition(saved.carbohydrates ?? null)} · F {formatNutrition(
                    saved.fat ?? null
                  )} · P {formatNutrition(saved.protein ?? null)}
                </p>
              </div>
            </Card.Content>
            <Card.Footer class="grid grid-cols-[1fr_1fr_auto] gap-2 border-t pt-4">
              <Button href={logHref(saved)} class="h-10">Log</Button>
              <Dialog.Trigger
                class={buttonVariants({ variant: "outline", class: "h-10" })}
                onclick={() => editProduct(saved)}><Pencil /> Edit</Dialog.Trigger
              >
              <form
                method="POST"
                action="?/delete"
                use:enhance={deleteEnhance}
                onsubmit={(event) => {
                  if (!confirm(`Delete ${saved.title}? Existing diary entries will be kept.`))
                    event.preventDefault();
                }}
              >
                <input type="hidden" name="id" value={saved.id} />
                <Button
                  type="submit"
                  variant="ghost"
                  size="icon"
                  class="text-destructive size-10"
                  aria-label={`Delete ${saved.title}`}><Trash2 /></Button
                >
              </form>
            </Card.Footer>
          </Card.Root>
        {/each}
      </div>

      <div class="hidden overflow-hidden rounded-xl border md:block">
        <table class="w-full text-sm">
          <thead class="bg-muted/50 text-left">
            <tr>
              <th class="px-4 py-3 font-medium">Product</th>
              <th class="px-4 py-3 font-medium">Nutrition</th>
              <th class="px-4 py-3 font-medium">Barcode</th>
              <th class="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            {#each data.products as saved (saved.id)}
              <tr>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    {#if saved.image_url}<img
                        src={saved.image_url}
                        alt=""
                        class="size-11 rounded-md bg-white object-contain"
                      />{:else}<span class="bg-muted grid size-11 place-items-center rounded-md"
                        ><Package class="size-5" /></span
                      >{/if}
                    <div class="min-w-0">
                      <p class="font-medium">{saved.title}</p>
                      {#if saved.brand}<p class="text-muted-foreground text-xs">
                          {saved.brand}
                        </p>{/if}
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <p class="font-medium">{formatNutrition(saved.calories)} kcal</p>
                  <p class="text-muted-foreground text-xs">
                    {nutritionBasisLabels[nutritionBasis(saved)]} · C {formatNutrition(
                      saved.carbohydrates ?? null
                    )} · F {formatNutrition(saved.fat ?? null)} · P {formatNutrition(
                      saved.protein ?? null
                    )}
                  </p>
                </td>
                <td class="text-muted-foreground px-4 py-3 font-mono text-xs"
                  >{saved.barcode ?? "—"}</td
                >
                <td class="px-4 py-3">
                  <div class="flex justify-end gap-2">
                    <Button href={logHref(saved)} size="sm">Log</Button>
                    <Dialog.Trigger
                      class={buttonVariants({ variant: "outline", size: "sm" })}
                      onclick={() => editProduct(saved)}><Pencil /> Edit</Dialog.Trigger
                    >
                    <form
                      method="POST"
                      action="?/delete"
                      use:enhance={deleteEnhance}
                      onsubmit={(event) => {
                        if (!confirm(`Delete ${saved.title}? Existing diary entries will be kept.`))
                          event.preventDefault();
                      }}
                    >
                      <input type="hidden" name="id" value={saved.id} />
                      <Button
                        type="submit"
                        variant="ghost"
                        size="icon"
                        class="text-destructive"
                        aria-label={`Delete ${saved.title}`}><Trash2 /></Button
                      >
                    </form>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

  <Dialog.Content class="barcode-review-dialog max-h-[92vh] overflow-y-auto sm:max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>{editing ? "Edit product" : "Review product"}</Dialog.Title>
      <Dialog.Description>Copy the values exactly as shown on the package label.</Dialog.Description
      >
    </Dialog.Header>

    {#if actionError || lookupError}
      <Alert.Root variant="destructive">
        <CircleAlert />
        <Alert.Title>{lookupError ? "Enter the product manually" : "Unable to save"}</Alert.Title>
        <Alert.Description>{actionError || lookupError}</Alert.Description>
      </Alert.Root>
    {/if}

    {#if barcodePreview}
      <Alert.Root class="border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30">
        <Barcode />
        <Alert.Title>Barcode result needs review</Alert.Title>
        <Alert.Description>
          {#if barcodePreview.missing_nutrients.length}
            Missing: {barcodePreview.missing_nutrients.join(", ")}. Leave unknown macros blank, but
            calories are required.
          {:else}
            Confirm the nutrition basis, serving size, package size, and values against the label.
          {/if}
        </Alert.Description>
      </Alert.Root>
    {/if}

    <form
      method="POST"
      action={editing ? "?/update" : "?/create"}
      use:productEnhance
      class="space-y-5"
    >
      <input type="hidden" name="id" value={$productData.id} />
      <input type="hidden" name="image_url" value={$productData.image_url} />
      {#if !editing}
        <Button
          type="button"
          variant="outline"
          class="w-full"
          onclick={() => openBarcodeScanner(true)}
        >
          <ScanLine /> Scan product barcode
        </Button>
      {/if}
      <div class="grid gap-4 sm:grid-cols-2">
        <Field form={productForm} name="title">
          <div class="space-y-2 sm:col-span-2">
            <Control>
              {#snippet children({ props })}
                <Label>Name</Label>
                <Input {...props} bind:value={$productData.title} maxlength={255} />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="brand">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Brand</Label>
                <Input {...props} bind:value={$productData.brand} maxlength={255} />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="barcode">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Barcode</Label>
                <Input
                  {...props}
                  bind:value={$productData.barcode}
                  inputmode="numeric"
                  maxlength={24}
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="nutrition_basis">
          <div class="space-y-2 sm:col-span-2">
            <Control>
              {#snippet children({ props })}
                <Label>Values shown on label</Label>
                <select
                  {...props}
                  bind:value={$productData.nutrition_basis}
                  class="border-input bg-background h-11 w-full rounded-md border px-3"
                >
                  {#each nutritionBases as basis}
                    <option value={basis}>{nutritionBasisLabels[basis]}</option>
                  {/each}
                </select>
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
      </div>

      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Field form={productForm} name="calories">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Calories</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  bind:value={$productData.calories}
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="carbohydrates">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Carbs (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  bind:value={$productData.carbohydrates}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="fat">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Fat (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  bind:value={$productData.fat}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
        <Field form={productForm} name="protein">
          <div class="space-y-2">
            <Control>
              {#snippet children({ props })}
                <Label>Protein (g)</Label>
                <Input
                  {...props}
                  type="number"
                  min="0"
                  step="0.1"
                  bind:value={$productData.protein}
                  placeholder="Unknown"
                />
              {/snippet}
            </Control>
            <FieldErrors />
          </div>
        </Field>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <fieldset class="grid grid-cols-[minmax(0,1fr)_6rem] gap-2 rounded-lg border p-3">
          <legend class="px-1 text-sm font-medium">Serving size (optional)</legend>
          <Field form={productForm} name="serving_size">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Serving size</Label>
                  <Input
                    {...props}
                    type="number"
                    min="0.01"
                    step="0.01"
                    bind:value={$productData.serving_size}
                    placeholder="e.g. 125"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
          <Field form={productForm} name="serving_size_unit">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Unit</Label>
                  <select
                    {...props}
                    aria-label="Serving size unit"
                    bind:value={$productData.serving_size_unit}
                    class="border-input bg-background h-10 w-full rounded-md border px-2"
                  >
                    <option value="g">g</option><option value="ml">ml</option>
                  </select>
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
        </fieldset>
        <fieldset class="grid grid-cols-[minmax(0,1fr)_6rem] gap-2 rounded-lg border p-3">
          <legend class="px-1 text-sm font-medium">Package size (optional)</legend>
          <Field form={productForm} name="package_size">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Package size</Label>
                  <Input
                    {...props}
                    type="number"
                    min="0.01"
                    step="0.01"
                    bind:value={$productData.package_size}
                    placeholder="e.g. 350"
                  />
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
          <Field form={productForm} name="package_size_unit">
            <div class="space-y-2">
              <Control>
                {#snippet children({ props })}
                  <Label>Unit</Label>
                  <select
                    {...props}
                    aria-label="Package size unit"
                    bind:value={$productData.package_size_unit}
                    class="border-input bg-background h-10 w-full rounded-md border px-2"
                  >
                    <option value="g">g</option><option value="ml">ml</option>
                  </select>
                {/snippet}
              </Control>
              <FieldErrors />
            </div>
          </Field>
        </fieldset>
      </div>

      <Dialog.Footer class="gap-2 [&>button]:h-11 [&>button]:w-full sm:[&>button]:w-auto">
        <Button type="button" variant="outline" onclick={() => (productOpen = false)}>Cancel</Button
        >
        <Button type="submit" disabled={$submitting}>
          {#if $submitting}<LoaderCircle class="animate-spin" />{/if}
          {editing ? "Save changes" : "Save product"}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

<BarcodeScannerDialog
  bind:open={scanOpen}
  loading={lookupLoading}
  onDetected={lookupBarcode}
  title="Scan a product"
  description="Use the camera or enter the barcode. You will review everything before saving."
/>

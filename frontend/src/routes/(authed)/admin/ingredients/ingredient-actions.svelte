<script lang="ts">
  import Button, { buttonVariants } from "$lib/components/ui/button/button.svelte";
  import { Pencil, Trash2, TriangleAlert } from "@lucide/svelte";
  import { enhance } from "$app/forms";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import { Input } from "$lib/components/ui/input";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { untrack } from "svelte";

  import type { IngredientPublic } from "$lib/client";
  import type { SuperForm } from "sveltekit-superforms";
  import type { Infer } from "sveltekit-superforms";
  import type { IngredientUpdateSchema } from "$lib/schemas/schemas";

  let {
    ingredient,
    updateForm
  }: {
    ingredient: IngredientPublic;
    updateForm: SuperForm<Infer<typeof IngredientUpdateSchema>>;
  } = $props();

  const { form: formData, enhance: formEnhance, message } = untrack(() => updateForm);

  let editOpen = $state(false);

  function openEdit() {
    formData.update(($f) => ({
      ...$f,
      id: ingredient.id,
      title: ingredient.title,
      calories: ingredient.calories,
      carbohydrates: ingredient.carbohydrates,
      fat: ingredient.fat,
      protein: ingredient.protein,
      weight_per_piece: ingredient.weight_per_piece,
      barcode: ingredient.barcode ?? ""
    }));
    editOpen = true;
  }

  $effect(() => {
    if ($message && editOpen) {
      if ($message.includes("successfully")) {
        editOpen = false;
      }
    }
  });
</script>

<div class="flex items-center justify-end gap-2">
  <Dialog.Root bind:open={editOpen}>
    <Dialog.Trigger
      class={buttonVariants({ variant: "ghost", size: "sm", class: "p-2" })}
      onclick={openEdit}
      aria-label={`Edit ${ingredient.title}`}
      title="Edit ingredient"
    >
      <Pencil />
    </Dialog.Trigger>
    <Dialog.Content class="sm:max-w-[425px]">
      <Dialog.Header>
        <Dialog.Title>Edit Ingredient</Dialog.Title>
        <Dialog.Description>Update the ingredient details below.</Dialog.Description>
      </Dialog.Header>
      <form method="POST" action="?/update" use:formEnhance class="space-y-4 py-4">
        <input type="hidden" name="id" value={$formData.id} />
        <input type="hidden" name="barcode" value={$formData.barcode ?? ""} />

        {#if $message && !$message.includes("successfully")}
          <Alert.Root variant="destructive">
            <TriangleAlert />
            <Alert.Title>Unable to update ingredient</Alert.Title>
            <Alert.Description>{$message}</Alert.Description>
          </Alert.Root>
        {/if}

        <Field form={updateForm} name="title">
          <Control>
            {#snippet children({ props })}
              <Label>Name</Label>
              <Input {...props} bind:value={$formData.title} placeholder="Enter ingredient name" />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Field form={updateForm} name="calories">
          <Control>
            {#snippet children({ props })}
              <Label>Calories (per 100g)</Label>
              <Input
                {...props}
                type="number"
                bind:value={$formData.calories}
                placeholder="Enter calories"
                min="0"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Field form={updateForm} name="carbohydrates">
          <Control>
            {#snippet children({ props })}
              <Label>Carbohydrates (per 100g)</Label>
              <Input
                {...props}
                type="number"
                bind:value={$formData.carbohydrates}
                placeholder="Enter carbohydrates"
                min="0"
                step="0.1"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Field form={updateForm} name="fat">
          <Control>
            {#snippet children({ props })}
              <Label>Fat (per 100g)</Label>
              <Input
                {...props}
                type="number"
                bind:value={$formData.fat}
                placeholder="Enter fat"
                min="0"
                step="0.1"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Field form={updateForm} name="protein">
          <Control>
            {#snippet children({ props })}
              <Label>Protein (per 100g)</Label>
              <Input
                {...props}
                type="number"
                bind:value={$formData.protein}
                placeholder="Enter protein"
                min="0"
                step="0.1"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Field form={updateForm} name="weight_per_piece">
          <Control>
            {#snippet children({ props })}
              <Label>Weight per piece (g)</Label>
              <Input
                {...props}
                type="number"
                bind:value={$formData.weight_per_piece}
                placeholder="Enter weight per piece"
                min="1"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Dialog.Footer>
          <Button type="submit">Update Ingredient</Button>
        </Dialog.Footer>
      </form>
    </Dialog.Content>
  </Dialog.Root>

  <AlertDialog.Root>
    <AlertDialog.Trigger>
      {#snippet child({ props })}
        <Button
          {...props}
          variant="ghost"
          title="Delete ingredient"
          aria-label={`Delete ${ingredient.title}`}
          size="sm"
          class="text-destructive hover:bg-destructive/10 hover:text-destructive p-2"
        >
          <Trash2 />
        </Button>
      {/snippet}
    </AlertDialog.Trigger>
    <AlertDialog.Content>
      <AlertDialog.Header>
        <AlertDialog.Title>Delete {ingredient.title}?</AlertDialog.Title>
        <AlertDialog.Description>
          This permanently removes the ingredient from the database. This action cannot be undone.
        </AlertDialog.Description>
      </AlertDialog.Header>
      <AlertDialog.Footer>
        <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
        <form action="?/delete" method="POST" use:enhance>
          <input type="hidden" name="id" value={ingredient.id} />
          <AlertDialog.Action type="submit" variant="destructive"
            >Delete ingredient</AlertDialog.Action
          >
        </form>
      </AlertDialog.Footer>
    </AlertDialog.Content>
  </AlertDialog.Root>
</div>

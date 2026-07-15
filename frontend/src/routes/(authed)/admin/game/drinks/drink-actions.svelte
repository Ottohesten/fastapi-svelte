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

  import type { DrinkPublic } from "$lib/client";
  import type { SuperForm, Infer } from "sveltekit-superforms";
  import type { DrinkUpdateSchema } from "$lib/schemas/schemas";

  let {
    drink,
    updateForm
  }: {
    drink: DrinkPublic;
    updateForm: SuperForm<Infer<typeof DrinkUpdateSchema>>;
  } = $props();

  const { form: formData, enhance: formEnhance, message } = untrack(() => updateForm);

  let editOpen = $state(false);

  function openEdit() {
    formData.update(($f) => ({
      ...$f,
      id: drink.id,
      name: drink.name
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
      aria-label={`Edit ${drink.name}`}
      title="Edit drink"
    >
      <Pencil />
    </Dialog.Trigger>
    <Dialog.Content class="sm:max-w-[425px]">
      <Dialog.Header>
        <Dialog.Title>Edit Drink</Dialog.Title>
        <Dialog.Description>Update the drink name below.</Dialog.Description>
      </Dialog.Header>
      <form method="POST" action="?/updateDrink" use:formEnhance class="space-y-4 py-4">
        <input type="hidden" name="id" value={$formData.id} />

        {#if $message && !$message.includes("successfully")}
          <Alert.Root variant="destructive">
            <TriangleAlert />
            <Alert.Title>Unable to update drink</Alert.Title>
            <Alert.Description>{$message}</Alert.Description>
          </Alert.Root>
        {/if}

        <Field form={updateForm} name="name">
          <Control>
            {#snippet children({ props })}
              <Label>Name</Label>
              <Input {...props} bind:value={$formData.name} placeholder="Enter drink name" />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>

        <Dialog.Footer>
          <Button type="submit">Update Drink</Button>
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
          title="Delete drink"
          aria-label={`Delete ${drink.name}`}
          size="sm"
          class="text-destructive hover:bg-destructive/10 hover:text-destructive p-2"
        >
          <Trash2 />
        </Button>
      {/snippet}
    </AlertDialog.Trigger>
    <AlertDialog.Content>
      <AlertDialog.Header>
        <AlertDialog.Title>Delete {drink.name}?</AlertDialog.Title>
        <AlertDialog.Description>
          This permanently removes the drink from the game catalogue. This action cannot be undone.
        </AlertDialog.Description>
      </AlertDialog.Header>
      <AlertDialog.Footer>
        <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
        <form action="?/deleteDrink" method="POST" use:enhance>
          <input type="hidden" name="drink_id" value={drink.id} />
          <AlertDialog.Action type="submit" variant="destructive">Delete drink</AlertDialog.Action>
        </form>
      </AlertDialog.Footer>
    </AlertDialog.Content>
  </AlertDialog.Root>
</div>

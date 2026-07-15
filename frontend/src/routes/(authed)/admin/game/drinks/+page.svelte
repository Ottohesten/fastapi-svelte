<script lang="ts">
  let { data } = $props();
  import DataTable from "$lib/components/ui/data-table.svelte";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import Button, { buttonVariants } from "$lib/components/ui/button/button.svelte";
  import { enhance } from "$app/forms";
  import { createColumns } from "./columns.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Input } from "$lib/components/ui/input";
  import { superForm } from "sveltekit-superforms";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import { DrinkSchema, DrinkUpdateSchema } from "$lib/schemas/schemas";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { CircleCheck, TriangleAlert } from "@lucide/svelte";

  let open = $state(false);

  const form = superForm(
    untrack(() => data.drinkCreateForm),
    {
      id: "drinkCreateForm",
      validators: zodClient(DrinkSchema),
      resetForm: true,
      onUpdated: ({ form }) => {
        if (form.valid && form.message) {
          open = false;
        }
      }
    }
  );

  const updateForm = superForm(
    untrack(() => data.drinkUpdateForm),
    {
      id: "drinkUpdateForm",
      validators: zodClient(DrinkUpdateSchema),
      resetForm: false, // manual population
      onUpdated: ({ form }) => {
        if (form.valid && form.message) {
          console.log("Update form valid:", form.message);
        }
      }
    }
  );

  const { form: formData, enhance: formEnhance, message } = form;
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

<div class="mx-auto max-w-7xl space-y-6">
  <AdminPageHeader title="Drinks" description="Manage the drinks available in game sessions.">
    {#snippet action()}
      <Dialog.Root bind:open>
        <Dialog.Trigger class={`${buttonVariants({ variant: "default" })} w-full sm:w-auto`}>
          Add drink
        </Dialog.Trigger>
        <Dialog.Content class="sm:max-w-[425px]">
          <Dialog.Header>
            <Dialog.Title>Add New Drink</Dialog.Title>
            <Dialog.Description>
              Add a new drink to the game. Enter the drink name below.
            </Dialog.Description>
          </Dialog.Header>
          <form method="POST" action="?/createDrink" use:formEnhance class="space-y-4 py-4">
            {#if $message && !$message.includes("successfully")}
              <Alert.Root variant="destructive">
                <TriangleAlert />
                <Alert.Title>Unable to add drink</Alert.Title>
                <Alert.Description>{$message}</Alert.Description>
              </Alert.Root>
            {/if}

            <Field {form} name="name">
              <Control>
                {#snippet children({ props })}
                  <Label>Name</Label>
                  <Input {...props} bind:value={$formData.name} placeholder="Enter drink name" />
                {/snippet}
              </Control>
              <FieldErrors />
            </Field>

            <Dialog.Footer class="[&>button]:w-full sm:[&>button]:w-auto">
              <Button type="submit">Add Drink</Button>
            </Dialog.Footer>
          </form>
        </Dialog.Content>
      </Dialog.Root>
    {/snippet}
  </AdminPageHeader>

  <div class="space-y-3">
    {#if $message && $message.includes("successfully")}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>Drink added</Alert.Title>
          <Alert.Description>{$message}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}

    {#if $updateMessage && $updateMessage.includes("successfully")}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>Drink updated</Alert.Title>
          <Alert.Description>{$updateMessage}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}
  </div>

  <DataTable
    data={data.drinks}
    {columns}
    searchColumn="name"
    searchPlaceholder="Filter drinks..."
  />
</div>

<!-- {JSON.stringify(data.drinks)} -->

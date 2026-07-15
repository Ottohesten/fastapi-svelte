<script lang="ts">
  import DataTable from "$lib/components/ui/data-table.svelte";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import { createColumns } from "./columns.js";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button, buttonVariants } from "$lib/components/ui/button";
  import { Checkbox } from "$lib/components/ui/checkbox/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { superForm } from "sveltekit-superforms";
  import { fade } from "svelte/transition";
  import { zod4 as zodClient } from "sveltekit-superforms/adapters";
  import { untrack } from "svelte";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { Input } from "$lib/components/ui/input/index.js";
  import { CircleCheck, TriangleAlert } from "@lucide/svelte";

  import { UserSchema, UserUpdateSchema, UserAddRoleSchema } from "$lib/schemas/schemas.js";
  let { data } = $props();
  let dialogOpen = $state(false);

  const form = superForm(
    untrack(() => data.userCreateForm),
    {
      id: "userCreateForm",
      validators: zodClient(UserSchema),
      onUpdated: ({ form }) => {
        if (form.valid) {
          dialogOpen = false;
        }
      }
    }
  );

  const userUpdateForm = superForm(
    untrack(() => data.userUpdateForm),
    {
      id: "userUpdateForm",
      dataType: "json",
      validators: zodClient(UserUpdateSchema)
      // Dialog close is handled by the row action component.
    }
  );

  const userAddRoleForm = superForm(
    untrack(() => data.userAddRoleForm),
    {
      id: "userAddRoleForm",
      validators: zodClient(UserAddRoleSchema)
    }
  );

  $effect(() => {
    if ($message) {
      const timer = setTimeout(() => {
        $message = undefined;
      }, 3000);
      return () => clearTimeout(timer);
    }
  });

  $effect(() => {
    if ($userUpdateMessage) {
      const timer = setTimeout(() => {
        $userUpdateMessage = undefined;
      }, 3000);
      return () => clearTimeout(timer);
    }
  });

  const { form: formData, enhance, errors, message } = form;

  const { errors: userUpdateErrors, message: userUpdateMessage } = userUpdateForm;

  // Create columns with the update form
  let columns = $derived(
    createColumns(userUpdateForm, userAddRoleForm, data.roles, data.availableScopes)
  );
</script>

<div class="mx-auto max-w-7xl space-y-6">
  <AdminPageHeader
    title="User management"
    description="Manage user accounts, access, and permissions."
  >
    {#snippet action()}
      <Dialog.Root bind:open={dialogOpen}>
        <Dialog.Trigger class={`${buttonVariants()} w-full sm:w-auto`}>Add User</Dialog.Trigger>
        <Dialog.Content class="sm:max-w-[500px]">
          <Dialog.Header>
            <Dialog.Title>Create New User</Dialog.Title>
            <Dialog.Description>
              Add a new user account to the system. All fields marked with * are required.
            </Dialog.Description>
          </Dialog.Header>
          <form action="?/createUser" method="POST" use:enhance class="space-y-4">
            <div class="grid grid-cols-1 gap-2">
              <Field {form} name="email">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium">Email *</Label>
                    <Input
                      {...props}
                      type="email"
                      bind:value={$formData.email}
                      placeholder="Enter user email"
                    />
                  {/snippet}
                </Control>
                <FieldErrors />
              </Field>

              <Field {form} name="full_name">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium">Full Name *</Label>
                    <Input
                      {...props}
                      type="text"
                      bind:value={$formData.full_name}
                      placeholder="Enter full name"
                    />
                  {/snippet}
                </Control>
                <FieldErrors />
              </Field>
              <Field {form} name="password">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium">Password *</Label>
                    <Input
                      {...props}
                      type="password"
                      bind:value={$formData.password}
                      placeholder="Enter user password"
                      autocomplete="new-password"
                    />
                  {/snippet}
                </Control>
                <FieldErrors />
              </Field>

              <Field {form} name="confirm_password">
                <Control>
                  {#snippet children({ props })}
                    <Label class="mb-1 block text-sm font-medium">Confirm Password *</Label>
                    <Input
                      {...props}
                      type="password"
                      bind:value={$formData.confirm_password}
                      placeholder="Confirm user password"
                      autocomplete="new-password"
                    />
                  {/snippet}
                </Control>
                <FieldErrors />
              </Field>

              <div class="space-y-3">
                <Field {form} name="is_active">
                  <Control>
                    {#snippet children({ props })}
                      <div class="flex items-center gap-2">
                        <Checkbox {...props} bind:checked={$formData.is_active} />
                        <Label for={props.id} class="text-sm">Active user</Label>
                      </div>
                    {/snippet}
                  </Control>
                  <FieldErrors />
                </Field>

                <Field {form} name="is_superuser">
                  <Control>
                    {#snippet children({ props })}
                      <div class="flex items-center gap-2">
                        <Checkbox {...props} bind:checked={$formData.is_superuser} />
                        <Label for={props.id} class="text-sm">Superuser</Label>
                      </div>
                    {/snippet}
                  </Control>
                  <FieldErrors />
                </Field>
              </div>
              <div class="flex flex-col-reverse gap-2 pt-4 sm:flex-row sm:justify-end">
                <Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
                  Cancel
                </Button>
                <Button type="submit">Create User</Button>
              </div>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Root>
    {/snippet}
  </AdminPageHeader>

  <div class="space-y-3">
    {#if $message}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>User saved</Alert.Title>
          <Alert.Description>{$message}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}

    {#if $userUpdateMessage}
      <div out:fade>
        <Alert.Root class="border-primary/20 bg-primary/5">
          <CircleCheck />
          <Alert.Title>User updated</Alert.Title>
          <Alert.Description>{$userUpdateMessage}</Alert.Description>
        </Alert.Root>
      </div>
    {/if}

    {#if $errors._errors}
      <Alert.Root variant="destructive">
        <TriangleAlert />
        <Alert.Title>Unable to create user</Alert.Title>
        <Alert.Description>
          {#each $errors._errors as error}
            <p>{error}</p>
          {/each}
        </Alert.Description>
      </Alert.Root>
    {/if}

    {#if $userUpdateErrors._errors}
      <Alert.Root variant="destructive">
        <TriangleAlert />
        <Alert.Title>Unable to update user</Alert.Title>
        <Alert.Description>
          {#each $userUpdateErrors._errors as error}
            <p>{error}</p>
          {/each}
        </Alert.Description>
      </Alert.Root>
    {/if}
  </div>

  <DataTable
    data={data.users.data}
    {columns}
    searchColumn="email"
    searchPlaceholder="Filter users by email..."
  />
  <!-- <div class="surface-2 rounded-2xl">
		<DataTable data={data.users.data} {columns} />
	</div> -->
</div>

<!-- <div>
	<p>
		Lorem ipsum dolor, sit amet consectetur adipisicing elit. Ratione at quo eveniet, nisi, placeat
		laborum distinctio autem provident rem reiciendis ex doloremque nobis, repellat dignissimos
		saepe accusantium eius neque assumenda!
	</p>
</div> -->

<!-- <div>
	<p>This is the admin users page</p>

	{JSON.stringify(data.users)}
</div> -->

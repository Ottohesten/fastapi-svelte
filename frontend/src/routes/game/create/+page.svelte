<script lang="ts">
  import { superForm } from "sveltekit-superforms";
  import { untrack } from "svelte";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";

  let { data } = $props();

  const form = superForm(
    untrack(() => data.form),
    {
      dataType: "json"
    }
  );

  const { form: formData, errors, message, constraints, enhance } = form;
</script>

<!-- <SuperDebug data={$form} /> -->

<div class="container mx-auto max-w-2xl p-4">
  <form method="POST" action="" enctype="multipart/form-data" use:enhance class="space-y-6">
    {#if $message}
      <h3 class="text-center text-2xl text-red-500">{$message}</h3>
    {/if}

    <Field {form} name="title">
      <Control>
        {#snippet children({ props })}
          <Label>Title</Label>
          <Input {...props} bind:value={$formData.title} placeholder="Game session title" />
        {/snippet}
      </Control>
      <FieldErrors />
    </Field>

    <div>
      <h1 class="mt-6 mb-2 text-xl font-semibold">Teams</h1>
      <hr class="border-gray-200 dark:border-gray-800" />
    </div>

    {#each $formData.teams as _, i}
      <div
        class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-800/50"
      >
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Team {i + 1}</h2>
          <button
            type="button"
            class="rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 transition-colors hover:border-red-300 hover:bg-red-100 focus:ring-2 focus:ring-red-500 focus:ring-offset-1 focus:outline-none dark:border-red-900/50 dark:bg-red-900/40 dark:text-red-300 dark:hover:border-red-800 dark:hover:bg-red-900/50"
            onclick={() => ($formData.teams = $formData.teams.filter((_, idx) => idx !== i))}
          >
            Remove
          </button>
        </div>
        <Field {form} name="teams[{i}].name">
          <Control>
            {#snippet children({ props })}
              <Label>Team Name</Label>
              <Input
                {...props}
                bind:value={$formData.teams[i].name}
                placeholder="Enter team name"
              />
            {/snippet}
          </Control>
          <FieldErrors />
        </Field>
      </div>
    {/each}

    <div class="flex gap-4">
      <Button
        variant="secondary"
        type="button"
        onclick={() => ($formData.teams = [...($formData.teams ?? []), { name: "", players: [] }])}
      >
        Add Team
      </Button>
      <Button type="submit">Submit</Button>
    </div>

    <div class="mt-5"></div>
  </form>
</div>

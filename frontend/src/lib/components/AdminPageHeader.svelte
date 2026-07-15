<script lang="ts">
  import type { Snippet } from "svelte";

  type AdminPageHeaderProps = {
    title: string;
    description: string;
    action?: Snippet;
  };

  let { title, description, action }: AdminPageHeaderProps = $props();
</script>

<header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
  <div class="min-w-0 space-y-1">
    <h1 class="text-foreground mb-0 text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
    <p class="text-muted-foreground max-w-2xl text-sm sm:text-base">{description}</p>
  </div>

  {#if action}
    <div class="w-full shrink-0 sm:w-auto">
      {@render action()}
    </div>
  {/if}
</header>

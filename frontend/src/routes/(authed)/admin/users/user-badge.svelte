<script lang="ts">
  import { Shield, User } from "lucide-svelte";

  let { isSuperuser }: { isSuperuser: boolean } = $props();
</script>

{#if isSuperuser}
  <span
    class="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800"
  >
    <Shield class="mr-1 h-3 w-3" />
    Admin
  </span>
{:else}
  <span
    class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
  >
    <User class="mr-1 h-3 w-3" />
    User
  </span>
{/if}

<script lang="ts">
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Shield, User } from "@lucide/svelte";

  let { isSuperuser }: { isSuperuser: boolean } = $props();
</script>

{#if isSuperuser}
  <Badge>
    <Shield />
    Admin
  </Badge>
{:else}
  <Badge variant="outline">
    <User />
    User
  </Badge>
{/if}

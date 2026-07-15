<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import { ArrowLeft, Gamepad2, GlassWater } from "@lucide/svelte";
</script>

<div class="mx-auto max-w-3xl space-y-6">
  <AdminPageHeader
    title="Game sessions"
    description="Session administration currently lives on the main game pages."
  />

  <Card.Root>
    <Card.Header>
      <Card.Title>Manage sessions from the game area</Card.Title>
      <Card.Description>
        Use the game overview to create or open a session. Drink options can still be maintained
        from the admin workspace.
      </Card.Description>
      <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
        <Gamepad2 class="size-5" />
      </Card.Action>
    </Card.Header>
    <Card.Content class="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
      <Button href="/game">
        <Gamepad2 /> View game sessions
      </Button>
      <Button href="/admin/game/drinks" variant="outline">
        <GlassWater /> Manage drinks
      </Button>
      <Button href="/admin" variant="ghost">
        <ArrowLeft /> Back to overview
      </Button>
    </Card.Content>
  </Card.Root>
</div>

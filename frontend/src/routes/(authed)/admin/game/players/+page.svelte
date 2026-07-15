<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import { ArrowLeft, Gamepad2, Users } from "@lucide/svelte";
</script>

<div class="mx-auto max-w-3xl space-y-6">
  <AdminPageHeader
    title="Players"
    description="Players are managed in the context of an individual game session."
  />

  <Card.Root>
    <Card.Header>
      <Card.Title>Choose a game session first</Card.Title>
      <Card.Description>
        Open a session to view its players, teams, and current drink assignments. There is no
        separate global player directory.
      </Card.Description>
      <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
        <Users class="size-5" />
      </Card.Action>
    </Card.Header>
    <Card.Content class="flex flex-col gap-3 sm:flex-row">
      <Button href="/game">
        <Gamepad2 /> View game sessions
      </Button>
      <Button href="/admin" variant="outline">
        <ArrowLeft /> Back to overview
      </Button>
    </Card.Content>
  </Card.Root>
</div>

<script lang="ts">
  import { enhance as enhanceAction } from "$app/forms";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import CircleAlert from "@lucide/svelte/icons/circle-alert";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import GlassWater from "@lucide/svelte/icons/glass-water";
  import Layers3 from "@lucide/svelte/icons/layers-3";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import UserPlus from "@lucide/svelte/icons/user-plus";
  import UserRound from "@lucide/svelte/icons/user-round";
  import UsersRound from "@lucide/svelte/icons/users-round";
  import { untrack } from "svelte";
  import { Control, Field, FieldErrors, Label } from "formsnap";
  import { superForm } from "sveltekit-superforms";
  import * as Alert from "$lib/components/ui/alert";
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import * as Select from "$lib/components/ui/select";
  import { getPlayerDrinkTotal } from "$lib/game/stats";
  import type { ActionData, PageData } from "./$types";

  const NO_TEAM = "__no_team__";

  let { data, form: actionResult }: { data: PageData; form: ActionData } = $props();

  const teamForm = superForm(
    untrack(() => data.teamForm),
    {
      dataType: "json",
      resetForm: true
    }
  );
  const {
    form: teamFormData,
    message: teamMessage,
    enhance: enhanceTeam,
    submitting: teamSubmitting
  } = teamForm;

  const playerForm = superForm(
    untrack(() => data.playerForm),
    {
      dataType: "json",
      resetForm: true
    }
  );
  const {
    form: playerFormData,
    message: playerMessage,
    enhance: enhancePlayer,
    submitting: playerSubmitting
  } = playerForm;

  const selectedTeamValue = $derived($playerFormData.team_id || NO_TEAM);
  const selectedTeamName = $derived(
    data.game_session.teams.find((team) => team.id === $playerFormData.team_id)?.name ?? "No team"
  );
  const assignedPlayerCount = $derived(
    data.game_session.players.filter((player) => player.team_id).length
  );
  const totalDrinks = $derived(
    data.game_session.players.reduce((total, player) => total + getPlayerDrinkTotal(player), 0)
  );
  const deletionError = $derived(
    actionResult && "error" in actionResult && typeof actionResult.error === "string"
      ? actionResult.error
      : null
  );

  function handleTeamSelection(teamId: string | undefined) {
    $playerFormData.team_id = !teamId || teamId === NO_TEAM ? undefined : teamId;
  }

  function playersForTeam(teamId: string) {
    return data.game_session.players.filter((player) => player.team_id === teamId);
  }

  function initials(name: string) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    return ((parts[0]?.[0] ?? "?") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : ""))
      .slice(0, 2)
      .toUpperCase();
  }
</script>

<svelte:head>
  <title>Manage {data.game_session.title}</title>
</svelte:head>

<div class="container space-y-6 py-6 sm:space-y-8 sm:py-10">
  <Button href={`/game/${data.game_session.id}`} variant="ghost" class="w-fit">
    <ArrowLeft />
    Back to game
  </Button>

  <header
    class="from-primary/15 via-primary/5 border-border relative overflow-hidden rounded-2xl border bg-linear-to-br to-transparent p-6 sm:p-8"
  >
    <div class="bg-primary/15 absolute -top-20 -right-16 size-56 rounded-full blur-3xl"></div>
    <div class="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div class="max-w-3xl space-y-3">
        <Badge variant="secondary"><Layers3 /> Session control</Badge>
        <div>
          <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">Game Management</h1>
          <p class="text-muted-foreground mt-2 text-base sm:text-lg">
            Add teams, organize the roster, and keep {data.game_session.title} ready to play.
          </p>
        </div>
      </div>
      <Button href={`/game/${data.game_session.id}`} variant="outline" class="w-full sm:w-fit">
        View live dashboard
        <ExternalLink />
      </Button>
    </div>
  </header>

  <section aria-label="Session summary" class="grid gap-3 sm:grid-cols-3">
    <Card.Root size="sm">
      <Card.Content class="flex items-center gap-3">
        <div
          class="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg"
        >
          <Layers3 />
        </div>
        <div>
          <p class="text-muted-foreground text-xs font-medium tracking-wide uppercase">Teams</p>
          <p class="text-2xl font-semibold">{data.game_session.teams.length}</p>
        </div>
      </Card.Content>
    </Card.Root>
    <Card.Root size="sm">
      <Card.Content class="flex items-center gap-3">
        <div
          class="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg"
        >
          <UsersRound />
        </div>
        <div>
          <p class="text-muted-foreground text-xs font-medium tracking-wide uppercase">Players</p>
          <p class="text-2xl font-semibold">{data.game_session.players.length}</p>
          <p class="text-muted-foreground text-xs">{assignedPlayerCount} assigned</p>
        </div>
      </Card.Content>
    </Card.Root>
    <Card.Root size="sm">
      <Card.Content class="flex items-center gap-3">
        <div
          class="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg"
        >
          <GlassWater />
        </div>
        <div>
          <p class="text-muted-foreground text-xs font-medium tracking-wide uppercase">Drinks</p>
          <p class="text-2xl font-semibold">{totalDrinks}</p>
          <p class="text-muted-foreground text-xs">recorded in total</p>
        </div>
      </Card.Content>
    </Card.Root>
  </section>

  {#if deletionError}
    <Alert.Root variant="destructive">
      <CircleAlert />
      <Alert.Title>Nothing was deleted</Alert.Title>
      <Alert.Description>{deletionError}</Alert.Description>
    </Alert.Root>
  {/if}

  <section aria-labelledby="add-to-session-heading" class="space-y-4">
    <div>
      <h2 id="add-to-session-heading" class="text-2xl font-semibold tracking-tight">
        Add to the session
      </h2>
      <p class="text-muted-foreground mt-1">
        Create the structure first, then add players to the right team.
      </p>
    </div>

    <div class="grid items-start gap-4 lg:grid-cols-2">
      <Card.Root>
        <Card.Header class="border-b">
          <Card.Title class="flex items-center gap-2"><Layers3 /> Create Team</Card.Title>
          <Card.Description>Add a group that players can join.</Card.Description>
        </Card.Header>
        <Card.Content>
          <form method="POST" action="?/addTeam" use:enhanceTeam class="space-y-5">
            {#if $teamMessage}
              <Alert.Root>
                <Alert.Title>Team update</Alert.Title>
                <Alert.Description>{$teamMessage}</Alert.Description>
              </Alert.Root>
            {/if}

            <Field form={teamForm} name="name">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <Label for="new-team-name">Team Name</Label>
                    <Input
                      {...props}
                      id="new-team-name"
                      type="text"
                      placeholder="For example, Red Team"
                      bind:value={$teamFormData.name}
                      autocomplete="off"
                      required
                    />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors class="text-destructive mt-2 text-sm" />
            </Field>

            <Button type="submit" class="w-full sm:w-fit" disabled={$teamSubmitting}>
              <Plus />
              {$teamSubmitting ? "Adding team…" : "Add Team"}
            </Button>
          </form>
        </Card.Content>
      </Card.Root>

      <Card.Root>
        <Card.Header class="border-b">
          <Card.Title class="flex items-center gap-2"><UserPlus /> Create Player</Card.Title>
          <Card.Description
            >Add a player now; their team can always be changed later.</Card.Description
          >
        </Card.Header>
        <Card.Content>
          <form method="POST" action="?/addPlayer" use:enhancePlayer class="space-y-5">
            {#if $playerMessage}
              <Alert.Root>
                <Alert.Title>Player update</Alert.Title>
                <Alert.Description>{$playerMessage}</Alert.Description>
              </Alert.Root>
            {/if}

            <Field form={playerForm} name="name">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <Label for="new-player-name">Player Name</Label>
                    <Input
                      {...props}
                      id="new-player-name"
                      type="text"
                      placeholder="Enter player name"
                      bind:value={$playerFormData.name}
                      autocomplete="off"
                      required
                    />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors class="text-destructive mt-2 text-sm" />
            </Field>

            <Field form={playerForm} name="team_id">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <Label for="new-player-team">Team (Optional)</Label>
                    <Select.Root
                      type="single"
                      value={selectedTeamValue}
                      onValueChange={handleTeamSelection}
                    >
                      <Select.Trigger {...props} id="new-player-team" class="w-full">
                        {selectedTeamName}
                      </Select.Trigger>
                      <Select.Content>
                        <Select.Item value={NO_TEAM} label="No team">No team</Select.Item>
                        {#each data.game_session.teams as team (team.id)}
                          <Select.Item value={team.id} label={team.name}>{team.name}</Select.Item>
                        {/each}
                      </Select.Content>
                    </Select.Root>
                  </div>
                {/snippet}
              </Control>
              <FieldErrors class="text-destructive mt-2 text-sm" />
            </Field>

            <Button type="submit" class="w-full sm:w-fit" disabled={$playerSubmitting}>
              <UserPlus />
              {$playerSubmitting ? "Adding player…" : "Add Player"}
            </Button>
          </form>
        </Card.Content>
      </Card.Root>
    </div>
  </section>

  <section aria-labelledby="teams-heading" class="space-y-4">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 id="teams-heading" class="text-2xl font-semibold tracking-tight">Teams</h2>
        <p class="text-muted-foreground mt-1">Open a team to see its full roster and statistics.</p>
      </div>
      <Badge variant="outline">{data.game_session.teams.length} total</Badge>
    </div>

    {#if data.game_session.teams.length === 0}
      <Card.Root class="border-dashed bg-transparent py-10 text-center">
        <Card.Content class="space-y-3">
          <div class="bg-muted mx-auto flex size-12 items-center justify-center rounded-full">
            <Layers3 class="text-muted-foreground" />
          </div>
          <div>
            <h3 class="font-semibold">No teams yet</h3>
            <p class="text-muted-foreground mt-1 text-sm">
              Add the first team above, or keep players unassigned.
            </p>
          </div>
        </Card.Content>
      </Card.Root>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each data.game_session.teams as team (team.id)}
          {@const teamPlayers = playersForTeam(team.id)}
          <Card.Root data-testid="team-card" class="transition-shadow hover:shadow-md">
            <Card.Header>
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0 space-y-1">
                  <Card.Title>
                    <h3>
                      <a
                        href={`/game/${data.game_session.id}/team/${team.id}`}
                        class="hover:text-primary focus-visible:ring-ring rounded-sm outline-none focus-visible:ring-2"
                      >
                        {team.name}
                      </a>
                    </h3>
                  </Card.Title>
                  <Card.Description>
                    {teamPlayers.length}
                    {teamPlayers.length === 1 ? "player" : "players"}
                  </Card.Description>
                </div>
                <Badge variant="secondary"><Layers3 /> Team</Badge>
              </div>
            </Card.Header>
            <Card.Content class="flex min-h-12 items-center">
              {#if teamPlayers.length}
                <div class="flex flex-wrap gap-2" aria-label={`${team.name} roster`}>
                  {#each teamPlayers.slice(0, 4) as player (player.id)}
                    <Badge variant="outline">{player.name}</Badge>
                  {/each}
                  {#if teamPlayers.length > 4}
                    <Badge variant="outline">+{teamPlayers.length - 4} more</Badge>
                  {/if}
                </div>
              {:else}
                <p class="text-muted-foreground text-sm">No players assigned yet.</p>
              {/if}
            </Card.Content>
            <Card.Footer class="justify-between gap-2">
              <Button
                href={`/game/${data.game_session.id}/team/${team.id}`}
                variant="ghost"
                size="sm"
              >
                View team <ExternalLink />
              </Button>

              <AlertDialog.Root>
                <AlertDialog.Trigger>
                  {#snippet child({ props })}
                    <Button
                      {...props}
                      type="button"
                      variant="ghost"
                      size="sm"
                      class="text-destructive"
                    >
                      <Trash2 /> Delete
                    </Button>
                  {/snippet}
                </AlertDialog.Trigger>
                <AlertDialog.Content>
                  <AlertDialog.Header>
                    <AlertDialog.Title>Delete {team.name}?</AlertDialog.Title>
                    <AlertDialog.Description>
                      The team will be permanently removed. Its {teamPlayers.length}
                      {teamPlayers.length === 1 ? "player" : "players"} will remain in the session without
                      a team.
                    </AlertDialog.Description>
                  </AlertDialog.Header>
                  <AlertDialog.Footer>
                    <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
                    <form action="?/deleteTeam" method="POST" use:enhanceAction>
                      <input type="hidden" name="team_id" value={team.id} />
                      <AlertDialog.Action type="submit" variant="destructive">
                        Delete team
                      </AlertDialog.Action>
                    </form>
                  </AlertDialog.Footer>
                </AlertDialog.Content>
              </AlertDialog.Root>
            </Card.Footer>
          </Card.Root>
        {/each}
      </div>
    {/if}
  </section>

  <section aria-labelledby="players-heading" class="space-y-4">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 id="players-heading" class="text-2xl font-semibold tracking-tight">Players</h2>
        <p class="text-muted-foreground mt-1">
          Open a player to change their team and recorded drinks.
        </p>
      </div>
      <Badge variant="outline">{data.game_session.players.length} total</Badge>
    </div>

    {#if data.game_session.players.length === 0}
      <Card.Root class="border-dashed bg-transparent py-10 text-center">
        <Card.Content class="space-y-3">
          <div class="bg-muted mx-auto flex size-12 items-center justify-center rounded-full">
            <UsersRound class="text-muted-foreground" />
          </div>
          <div>
            <h3 class="font-semibold">No players yet</h3>
            <p class="text-muted-foreground mt-1 text-sm">
              Add the first player above to start building the roster.
            </p>
          </div>
        </Card.Content>
      </Card.Root>
    {:else}
      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {#each data.game_session.players as player (player.id)}
          {@const drinkTotal = getPlayerDrinkTotal(player)}
          <Card.Root data-testid="player-card" size="sm" class="transition-shadow hover:shadow-md">
            <Card.Content class="flex items-center gap-3">
              <Avatar.Root class="size-11 shrink-0">
                <Avatar.Fallback class="bg-primary/10 text-primary font-semibold">
                  {initials(player.name)}
                </Avatar.Fallback>
              </Avatar.Root>
              <div class="min-w-0 flex-1">
                <h3 class="truncate font-semibold">
                  <a
                    href={`/game/${data.game_session.id}/player/${player.id}`}
                    class="hover:text-primary focus-visible:ring-ring rounded-sm outline-none focus-visible:ring-2"
                  >
                    {player.name}
                  </a>
                </h3>
                <p class="text-muted-foreground truncate text-sm">
                  {#if player.team}
                    Team: {player.team.name}
                  {:else}
                    No team assigned
                  {/if}
                </p>
              </div>
              <Badge variant="outline" aria-label={`${drinkTotal} drinks recorded`}>
                <GlassWater />
                {drinkTotal}
              </Badge>
            </Card.Content>
            <Card.Footer class="justify-between gap-2">
              <Button
                href={`/game/${data.game_session.id}/player/${player.id}`}
                variant="ghost"
                size="sm"
              >
                <UserRound /> Manage
              </Button>

              <AlertDialog.Root>
                <AlertDialog.Trigger>
                  {#snippet child({ props })}
                    <Button
                      {...props}
                      type="button"
                      variant="ghost"
                      size="sm"
                      class="text-destructive"
                    >
                      <Trash2 /> Delete
                    </Button>
                  {/snippet}
                </AlertDialog.Trigger>
                <AlertDialog.Content>
                  <AlertDialog.Header>
                    <AlertDialog.Title>Delete {player.name}?</AlertDialog.Title>
                    <AlertDialog.Description>
                      This permanently removes the player and their recorded drink totals from the
                      session. This action cannot be undone.
                    </AlertDialog.Description>
                  </AlertDialog.Header>
                  <AlertDialog.Footer>
                    <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
                    <form action="?/deletePlayer" method="POST" use:enhanceAction>
                      <input type="hidden" name="player_id" value={player.id} />
                      <AlertDialog.Action type="submit" variant="destructive">
                        Delete player
                      </AlertDialog.Action>
                    </form>
                  </AlertDialog.Footer>
                </AlertDialog.Content>
              </AlertDialog.Root>
            </Card.Footer>
          </Card.Root>
        {/each}
      </div>
    {/if}
  </section>
</div>

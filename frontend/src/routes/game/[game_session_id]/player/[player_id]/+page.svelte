<script lang="ts">
  import { superForm } from "sveltekit-superforms";
  import { Field, Control, Label, FieldErrors } from "formsnap";
  import { untrack } from "svelte";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import CircleAlert from "@lucide/svelte/icons/circle-alert";
  import GlassWater from "@lucide/svelte/icons/glass-water";
  import Layers3 from "@lucide/svelte/icons/layers-3";
  import LockKeyhole from "@lucide/svelte/icons/lock-keyhole";
  import Save from "@lucide/svelte/icons/save";
  import Trophy from "@lucide/svelte/icons/trophy";
  import UserRound from "@lucide/svelte/icons/user-round";
  import * as Alert from "$lib/components/ui/alert";
  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import * as Select from "$lib/components/ui/select";
  import { getPlayerDrinkTotal, summarizeDrinks } from "$lib/game/stats";
  import type { PageData } from "./$types";

  const NO_TEAM = "__no_team__";

  let { data }: { data: PageData } = $props();

  const form = superForm(
    untrack(() => data.form),
    {
      dataType: "json"
    }
  );
  const { form: formData, errors, message, enhance, submitting } = form;

  const currentDrinkTotal = $derived(getPlayerDrinkTotal(data.player));
  const currentDrinkSummary = $derived(summarizeDrinks([data.player]));
  const currentTopDrink = $derived(currentDrinkSummary[0]);
  const currentMaxDrinkAmount = $derived(currentTopDrink?.amount ?? 0);
  const selectedDrinkCount = $derived($formData.drinks.length);
  const selectedTeamValue = $derived($formData.team_id ?? NO_TEAM);
  const selectedTeamName = $derived(
    data.game_session.teams.find((team) => team.id === $formData.team_id)?.name ?? "No team"
  );
  const canManage = $derived(Boolean(data.authenticatedUser?.scopes?.includes("games:update")));

  function initials(name: string) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    return (parts[0]?.[0] ?? "?") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : "");
  }

  function handleTeamSelection(teamId: string | undefined) {
    $formData.team_id = !teamId || teamId === NO_TEAM ? null : teamId;
  }

  function handleDrinkSelection(drinkId: string, isChecked: boolean) {
    const existingDrinkIndex = $formData.drinks.findIndex((drink) => drink.drink_id === drinkId);

    if (isChecked && existingDrinkIndex === -1) {
      $formData.drinks = [...$formData.drinks, { drink_id: drinkId, amount: 1 }];
    } else if (!isChecked && existingDrinkIndex !== -1) {
      $formData.drinks = $formData.drinks.filter((_, index) => index !== existingDrinkIndex);
    }
  }

  function handleAmountChange(drinkIndex: number) {
    const drink = $formData.drinks[drinkIndex];
    if (!drink) return;

    const amount = Number(drink.amount);
    drink.amount = Number.isFinite(amount) ? Math.max(1, Math.floor(amount)) : 1;
  }

  function currentDrinkPercentage(amount: number) {
    if (!currentDrinkTotal) return 0;
    return Math.round((amount / currentDrinkTotal) * 100);
  }

  function currentDrinkBarWidth(amount: number) {
    if (!currentMaxDrinkAmount) return 0;
    return Math.max(6, Math.round((amount / currentMaxDrinkAmount) * 100));
  }
</script>

<svelte:head>
  <title>{data.player.name} · {data.game_session.title}</title>
</svelte:head>

<div class="container space-y-6 py-6 sm:py-10">
  <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <Button href={`/game/${data.game_session.id}`} variant="ghost" class="w-fit">
      <ArrowLeft />
      Back to game
    </Button>

    {#if data.player.team_id}
      <Button href={`/game/${data.game_session.id}/team/${data.player.team_id}`} variant="outline">
        <Layers3 />
        View team
      </Button>
    {/if}
  </div>

  <header
    class="from-primary/15 via-primary/5 border-border relative overflow-hidden rounded-2xl border bg-linear-to-br to-transparent p-6 sm:p-8"
  >
    <div class="bg-primary/15 absolute -top-16 -right-16 size-48 rounded-full blur-3xl"></div>
    <div class="relative flex flex-col gap-5 sm:flex-row sm:items-center">
      <Avatar.Root class="size-16 border-4 border-background shadow-sm sm:size-20">
        <Avatar.Fallback
          class="bg-primary text-primary-foreground text-xl font-semibold sm:text-2xl"
        >
          {initials(data.player.name).toUpperCase()}
        </Avatar.Fallback>
      </Avatar.Root>
      <div class="min-w-0 space-y-2">
        <div class="flex flex-wrap items-center gap-2">
          <Badge variant="secondary"><UserRound /> Player</Badge>
          <Badge variant="outline">{data.player.team?.name ?? "No team"}</Badge>
        </div>
        <div>
          <h1 class="mb-0 truncate text-3xl font-bold tracking-tight sm:text-4xl">
            {data.player.name}
          </h1>
          <p class="text-muted-foreground mt-1">
            Player overview for
            <a
              href={`/game/${data.game_session.id}`}
              class="text-foreground font-medium underline-offset-4 hover:underline"
            >
              {data.game_session.title}
            </a>
          </p>
        </div>
      </div>
    </div>
  </header>

  <section aria-label="Player statistics" class="grid gap-4 sm:grid-cols-3">
    <Card.Root>
      <Card.Header>
        <Card.Title>Total drinks</Card.Title>
        <Card.Description>Currently recorded</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <GlassWater class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="text-3xl font-semibold tabular-nums">{currentDrinkTotal}</p>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Drink types</Card.Title>
        <Card.Description>Different drinks recorded</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <Layers3 class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="text-3xl font-semibold tabular-nums">{currentDrinkSummary.length}</p>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Top drink</Card.Title>
        <Card.Description>Largest current total</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <Trophy class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="truncate text-lg font-semibold">{currentTopDrink?.name ?? "None yet"}</p>
        {#if currentTopDrink}
          <p class="text-muted-foreground mt-1 text-sm">{currentTopDrink.amount} recorded</p>
        {/if}
      </Card.Content>
    </Card.Root>
  </section>

  <Card.Root>
    <Card.Header>
      <Card.Title>Current drink breakdown</Card.Title>
      <Card.Description>Recorded totals for this player.</Card.Description>
    </Card.Header>
    <Card.Content>
      {#if currentDrinkSummary.length}
        <div class="grid gap-x-8 gap-y-5 sm:grid-cols-2">
          {#each currentDrinkSummary as drink (drink.id)}
            <div class="space-y-2">
              <div class="flex items-center justify-between gap-3 text-sm">
                <span class="truncate font-medium">{drink.name}</span>
                <span class="text-muted-foreground shrink-0 tabular-nums">
                  {drink.amount} · {currentDrinkPercentage(drink.amount)}%
                </span>
              </div>
              <div class="bg-muted h-2 overflow-hidden rounded-full">
                <div
                  class="bg-primary h-full rounded-full"
                  style={`width: ${currentDrinkBarWidth(drink.amount)}%`}
                ></div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="text-muted-foreground grid min-h-32 place-items-center text-center">
          <div>
            <GlassWater class="mx-auto mb-3 size-8" />
            <p class="text-foreground font-medium">No drinks recorded</p>
            <p class="mt-1 text-sm">This player's totals will appear here during the game.</p>
          </div>
        </div>
      {/if}
    </Card.Content>
  </Card.Root>

  {#if canManage}
    {#if $message}
      <Alert.Root variant="destructive">
        <CircleAlert />
        <Alert.Title>Player update</Alert.Title>
        <Alert.Description>{$message}</Alert.Description>
      </Alert.Root>
    {/if}

    <form method="POST" use:enhance class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-[minmax(17rem,0.7fr)_minmax(0,1.3fr)]">
        <Card.Root class="h-fit">
          <Card.Header>
            <Card.Title>Player details</Card.Title>
            <Card.Description
              >Update the display name or move this player to a team.</Card.Description
            >
          </Card.Header>
          <Card.Content class="space-y-5">
            <Field {form} name="name">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <Label for="player-name">Player name</Label>
                    <Input
                      {...props}
                      id="player-name"
                      type="text"
                      bind:value={$formData.name}
                      placeholder="Enter player name"
                      autocomplete="off"
                      required
                    />
                  </div>
                {/snippet}
              </Control>
              <FieldErrors class="text-destructive mt-2 text-sm" />
            </Field>

            <Field {form} name="team_id">
              <Control>
                {#snippet children({ props })}
                  <div class="space-y-2">
                    <Label for="player-team">Team</Label>
                    <Select.Root
                      type="single"
                      value={selectedTeamValue}
                      onValueChange={handleTeamSelection}
                    >
                      <Select.Trigger {...props} id="player-team" class="w-full">
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
          </Card.Content>
        </Card.Root>

        <Card.Root>
          <Card.Header>
            <Card.Title>Drink totals</Card.Title>
            <Card.Description>
              Select drinks and set the complete recorded amount for each one.
            </Card.Description>
            <Card.Action>
              <Badge variant="secondary">{selectedDrinkCount} selected</Badge>
            </Card.Action>
          </Card.Header>
          <Card.Content>
            {#if typeof $errors.drinks === "string"}
              <p class="text-destructive mb-4 text-sm">{$errors.drinks}</p>
            {/if}

            {#if data.drinks?.length}
              <div class="grid gap-3 sm:grid-cols-2">
                {#each data.drinks as availableDrink (availableDrink.id)}
                  {@const selectedIndex = $formData.drinks.findIndex(
                    (drink) => drink.drink_id === availableDrink.id
                  )}
                  {@const isChecked = selectedIndex !== -1}
                  <div
                    class="border-border has-checked:border-primary/50 has-checked:bg-primary/5 rounded-xl border p-4 transition-colors"
                  >
                    <div class="flex items-start gap-3">
                      <input
                        type="checkbox"
                        id={`drink-checkbox-${availableDrink.id}`}
                        checked={isChecked}
                        onchange={(event) =>
                          handleDrinkSelection(
                            availableDrink.id,
                            (event.currentTarget as HTMLInputElement).checked
                          )}
                        class="accent-primary mt-0.5 size-5 shrink-0"
                      />
                      <div class="min-w-0 flex-1 space-y-3">
                        <label
                          for={`drink-checkbox-${availableDrink.id}`}
                          class="block cursor-pointer truncate font-medium"
                        >
                          {availableDrink.name}
                        </label>

                        {#if isChecked && $formData.drinks[selectedIndex]}
                          <div class="space-y-1.5">
                            <label
                              for={`drink-amount-${availableDrink.id}`}
                              class="text-xs font-medium"
                            >
                              Recorded amount
                            </label>
                            <Input
                              id={`drink-amount-${availableDrink.id}`}
                              type="number"
                              min="1"
                              step="1"
                              inputmode="numeric"
                              bind:value={$formData.drinks[selectedIndex].amount}
                              oninput={() => handleAmountChange(selectedIndex)}
                              aria-label={`Amount for ${availableDrink.name}`}
                            />
                          </div>
                        {/if}
                      </div>
                    </div>

                    {#if isChecked && $errors.drinks && $errors.drinks[selectedIndex]}
                      {@const drinkError = $errors.drinks[selectedIndex]}
                      <div class="text-destructive mt-2 text-xs">
                        {#if typeof drinkError === "string"}
                          {drinkError}
                        {:else if drinkError?.amount}
                          {drinkError.amount.join(" ")}
                        {:else if drinkError?.drink_id}
                          {drinkError.drink_id.join(" ")}
                        {/if}
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-muted-foreground grid min-h-44 place-items-center text-center">
                <div>
                  <GlassWater class="mx-auto mb-3 size-8" />
                  <p class="text-foreground font-medium">No drink options available</p>
                  <p class="mt-1 text-sm">An administrator can add drinks from the admin area.</p>
                </div>
              </div>
            {/if}
          </Card.Content>
        </Card.Root>
      </div>

      <div
        class="border-border bg-background/90 sticky bottom-3 z-10 flex flex-col-reverse gap-3 rounded-xl border p-3 shadow-lg backdrop-blur sm:flex-row sm:items-center sm:justify-between"
      >
        <p class="text-muted-foreground px-2 text-xs sm:text-sm">
          Saving replaces the current player details and drink totals.
        </p>
        <Button type="submit" class="sm:min-w-36" disabled={$submitting}>
          <Save />
          {$submitting ? "Saving…" : "Update player"}
        </Button>
      </div>
    </form>
  {:else}
    <Alert.Root>
      <LockKeyhole />
      <Alert.Title>Read-only player view</Alert.Title>
      <Alert.Description>
        Game-management access is required to change the player's name, team, or drink totals.
      </Alert.Description>
    </Alert.Root>
  {/if}
</div>

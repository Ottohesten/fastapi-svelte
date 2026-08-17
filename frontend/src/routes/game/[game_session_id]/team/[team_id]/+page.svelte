<script lang="ts">
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import ChartNoAxesColumnIncreasing from "@lucide/svelte/icons/chart-no-axes-column-increasing";
  import GlassWater from "@lucide/svelte/icons/glass-water";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import Trophy from "@lucide/svelte/icons/trophy";
  import Users from "@lucide/svelte/icons/users";
  import * as Avatar from "$lib/components/ui/avatar";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { getPlayerDrinkTotal, rankPlayersByDrinks, summarizeDrinks } from "$lib/game/stats";
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();

  const rankedPlayers = $derived(rankPlayersByDrinks(data.players));
  const drinkSummary = $derived(summarizeDrinks(data.players));
  const totalDrinks = $derived(
    data.players.reduce((total, player) => total + getPlayerDrinkTotal(player), 0)
  );
  const averageDrinks = $derived(data.players.length ? totalDrinks / data.players.length : 0);
  const leadingPlayer = $derived(rankedPlayers[0]);
  const topDrink = $derived(drinkSummary[0]);
  const maxDrinkAmount = $derived(topDrink?.amount ?? 0);
  const canManage = $derived(Boolean(data.authenticatedUser?.scopes?.includes("games:update")));

  function initials(name: string) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    return (parts[0]?.[0] ?? "?") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : "");
  }

  function percentage(amount: number) {
    if (!totalDrinks) return 0;
    return Math.round((amount / totalDrinks) * 100);
  }

  function barWidth(amount: number) {
    if (!maxDrinkAmount) return 0;
    return Math.max(6, Math.round((amount / maxDrinkAmount) * 100));
  }
</script>

<svelte:head>
  <title>{data.team.name} · {data.game_session.title}</title>
</svelte:head>

<div class="container space-y-6 py-6 sm:py-10">
  <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <Button href={`/game/${data.game_session.id}`} variant="ghost" class="w-fit">
      <ArrowLeft />
      Back to game
    </Button>

    {#if canManage}
      <Button href={`/game/${data.game_session.id}/update`} variant="outline">
        <Settings2 />
        Manage game
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
          {initials(data.team.name).toUpperCase()}
        </Avatar.Fallback>
      </Avatar.Root>
      <div class="min-w-0 space-y-2">
        <Badge variant="secondary"><Users /> Team</Badge>
        <div>
          <h1 class="mb-0 truncate text-3xl font-bold tracking-tight sm:text-4xl">
            {data.team.name}
          </h1>
          <p class="text-muted-foreground mt-1">
            Team overview for
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

  <section aria-label="Team statistics" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <Card.Root>
      <Card.Header>
        <Card.Title>Players</Card.Title>
        <Card.Description>Current team roster</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <Users class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="text-3xl font-semibold tabular-nums">{data.players.length}</p>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Total drinks</Card.Title>
        <Card.Description>Recorded by this team</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <GlassWater class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="text-3xl font-semibold tabular-nums">{totalDrinks}</p>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Average</Card.Title>
        <Card.Description>Drinks per player</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <ChartNoAxesColumnIncreasing class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="text-3xl font-semibold tabular-nums">{averageDrinks.toFixed(1)}</p>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Leading player</Card.Title>
        <Card.Description>Most recorded drinks</Card.Description>
        <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
          <Trophy class="size-5" />
        </Card.Action>
      </Card.Header>
      <Card.Content>
        <p class="truncate text-lg font-semibold">{leadingPlayer?.name ?? "No player yet"}</p>
        {#if leadingPlayer}
          <p class="text-muted-foreground mt-1 text-sm">
            {getPlayerDrinkTotal(leadingPlayer)} drinks
          </p>
        {/if}
      </Card.Content>
    </Card.Root>
  </section>

  <div class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(19rem,0.8fr)]">
    <Card.Root>
      <Card.Header>
        <Card.Title>Team roster</Card.Title>
        <Card.Description>Players are ordered by their recorded drink total.</Card.Description>
      </Card.Header>
      <Card.Content>
        {#if rankedPlayers.length}
          <div class="divide-border divide-y">
            {#each rankedPlayers as player, index (player.id)}
              {@const playerTotal = getPlayerDrinkTotal(player)}
              {@const playerTopDrink = summarizeDrinks([player])[0]}
              <a
                href={`/game/${data.game_session.id}/player/${player.id}`}
                class="hover:bg-muted/60 focus-visible:ring-ring -mx-2 flex items-center gap-3 rounded-lg px-2 py-4 transition-colors focus-visible:ring-2 focus-visible:outline-none"
              >
                <span class="text-muted-foreground w-6 text-center text-sm tabular-nums">
                  {index + 1}
                </span>
                <Avatar.Root class="size-10">
                  <Avatar.Fallback class="bg-primary/10 text-primary font-medium">
                    {initials(player.name).toUpperCase()}
                  </Avatar.Fallback>
                </Avatar.Root>
                <span class="min-w-0 flex-1">
                  <span class="block truncate font-medium">{player.name}</span>
                  <span class="text-muted-foreground block truncate text-xs sm:text-sm">
                    {playerTopDrink ? `Top drink: ${playerTopDrink.name}` : "No drinks recorded"}
                  </span>
                </span>
                <Badge variant={playerTotal ? "secondary" : "outline"}>
                  {playerTotal}
                  {playerTotal === 1 ? "drink" : "drinks"}
                </Badge>
              </a>
            {/each}
          </div>
        {:else}
          <div class="text-muted-foreground grid min-h-48 place-items-center text-center">
            <div>
              <Users class="mx-auto mb-3 size-8" />
              <p class="text-foreground font-medium">No players on this team yet</p>
              <p class="mt-1 text-sm">Players can be assigned from the game management page.</p>
            </div>
          </div>
        {/if}
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>Drink breakdown</Card.Title>
        <Card.Description>Combined totals across the team.</Card.Description>
      </Card.Header>
      <Card.Content>
        {#if drinkSummary.length}
          <div class="space-y-5">
            {#each drinkSummary as drink (drink.id)}
              <div class="space-y-2">
                <div class="flex items-center justify-between gap-3 text-sm">
                  <span class="truncate font-medium">{drink.name}</span>
                  <span class="text-muted-foreground shrink-0 tabular-nums">
                    {drink.amount} · {percentage(drink.amount)}%
                  </span>
                </div>
                <div class="bg-muted h-2 overflow-hidden rounded-full">
                  <div
                    class="bg-primary h-full rounded-full transition-[width]"
                    style={`width: ${barWidth(drink.amount)}%`}
                  ></div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-muted-foreground grid min-h-48 place-items-center text-center">
            <div>
              <GlassWater class="mx-auto mb-3 size-8" />
              <p class="text-foreground font-medium">Nothing recorded yet</p>
              <p class="mt-1 text-sm">Drink totals will appear here as the game progresses.</p>
            </div>
          </div>
        {/if}
      </Card.Content>
    </Card.Root>
  </div>
</div>

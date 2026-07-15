<script lang="ts">
  import type { TrafficData } from "$lib/analytics";
  import * as Card from "$lib/components/ui/card";
  import { CircleAlert, Clock3, Eye, UserCheck, UsersRound } from "@lucide/svelte";
  import TrafficChart from "./TrafficChart.svelte";

  let { traffic }: { traffic: TrafficData | null } = $props();

  const numberFormatter = new Intl.NumberFormat("en-DK");

  const formatCount = (value: number) => numberFormatter.format(value);
  const barWidth = (value: number, maximum: number) => {
    if (value <= 0 || maximum <= 0) return 0;
    return Math.max(2, (value / maximum) * 100);
  };

  let routeMaximum = $derived(
    traffic ? Math.max(0, ...traffic.top_routes.map((route) => route.page_views)) : 0
  );
  let identifiedPageViews = $derived(
    traffic ? traffic.authenticated_page_views_7d + traffic.anonymous_page_views_7d : 0
  );
  let authenticatedShare = $derived(
    traffic && identifiedPageViews > 0
      ? Math.round((traffic.authenticated_page_views_7d / identifiedPageViews) * 100)
      : null
  );
</script>

<section aria-labelledby="traffic-heading" class="space-y-4">
  <div>
    <h2 id="traffic-heading" class="mb-0 text-lg font-semibold">Traffic</h2>
    <p class="text-muted-foreground text-sm">Recent visits recorded by this application.</p>
  </div>

  {#if traffic === null}
    <Card.Root>
      <Card.Content class="flex items-start gap-3 py-2">
        <span class="bg-muted text-muted-foreground shrink-0 rounded-lg p-2">
          <CircleAlert class="size-5" aria-hidden="true" />
        </span>
        <div>
          <p class="font-medium">Traffic data is unavailable</p>
          <p class="text-muted-foreground mt-1 text-sm">
            The dashboard could not load analytics right now. Other administration features are
            unaffected.
          </p>
        </div>
      </Card.Content>
    </Card.Root>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card.Root size="sm">
        <Card.Header>
          <Card.Title>Page views</Card.Title>
          <Card.Description>Last 24 hours</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <Clock3 class="size-4" aria-hidden="true" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-2xl font-semibold tabular-nums">
            {formatCount(traffic.page_views_24h)}
          </p>
        </Card.Content>
      </Card.Root>

      <Card.Root size="sm">
        <Card.Header>
          <Card.Title>Page views</Card.Title>
          <Card.Description>Last 7 days</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <Eye class="size-4" aria-hidden="true" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-2xl font-semibold tabular-nums">
            {formatCount(traffic.page_views_7d)}
          </p>
        </Card.Content>
      </Card.Root>

      <Card.Root size="sm">
        <Card.Header>
          <Card.Title>Tab sessions</Card.Title>
          <Card.Description>One start per browser tab</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <UsersRound class="size-4" aria-hidden="true" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-2xl font-semibold tabular-nums">
            {formatCount(traffic.browser_sessions_7d)}
          </p>
        </Card.Content>
      </Card.Root>

      <Card.Root size="sm">
        <Card.Header>
          <Card.Title>Signed-in traffic</Card.Title>
          <Card.Description>Share of recorded views</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <UserCheck class="size-4" aria-hidden="true" />
          </Card.Action>
        </Card.Header>
        <Card.Content class="space-y-1">
          <p class="text-2xl font-semibold tabular-nums">
            {authenticatedShare === null ? "—" : `${authenticatedShare}%`}
          </p>
          <p class="text-muted-foreground text-xs">
            {formatCount(traffic.authenticated_page_views_7d)} signed in ·
            {formatCount(traffic.anonymous_page_views_7d)} anonymous
          </p>
        </Card.Content>
      </Card.Root>
    </div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.65fr)]">
      <Card.Root>
        <Card.Header>
          <Card.Title>Daily activity</Card.Title>
          <Card.Description>Page views and tab sessions during the last 7 days.</Card.Description>
        </Card.Header>
        <Card.Content class="min-w-0">
          {#if traffic.daily.length === 0}
            <p class="text-muted-foreground py-12 text-center text-sm">
              No daily traffic has been recorded yet.
            </p>
          {:else}
            <TrafficChart data={traffic.daily} />
          {/if}
        </Card.Content>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Top routes</Card.Title>
          <Card.Description>Most-viewed pages during the last 7 days.</Card.Description>
        </Card.Header>
        <Card.Content>
          {#if traffic.top_routes.length === 0}
            <p class="text-muted-foreground py-12 text-center text-sm">
              No route traffic has been recorded yet.
            </p>
          {:else}
            <ol class="space-y-4">
              {#each traffic.top_routes as route (route.route)}
                <li class="space-y-1.5">
                  <div class="flex items-baseline justify-between gap-3">
                    <span class="min-w-0 truncate font-mono text-xs" title={route.route}>
                      {route.route}
                    </span>
                    <span class="shrink-0 text-sm font-semibold tabular-nums">
                      {formatCount(route.page_views)}
                      <span class="sr-only">page views</span>
                    </span>
                  </div>
                  <div class="bg-primary/10 h-1.5 overflow-hidden rounded-full" aria-hidden="true">
                    <div
                      class="bg-primary h-full rounded-full"
                      style:width={`${barWidth(route.page_views, routeMaximum)}%`}
                    ></div>
                  </div>
                </li>
              {/each}
            </ol>
          {/if}
        </Card.Content>
      </Card.Root>
    </div>
  {/if}
</section>

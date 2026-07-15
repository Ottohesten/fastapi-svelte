<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount, untrack } from "svelte";
  import { isTrafficData, type TrafficData } from "$lib/analytics";
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import AdminPageHeader from "$lib/components/AdminPageHeader.svelte";
  import TrafficOverview from "./TrafficOverview.svelte";
  import {
    ArrowRight,
    BookOpen,
    ChefHat,
    CircleAlert,
    Gamepad2,
    GlassWater,
    ScanBarcode,
    UserRoundX,
    Users
  } from "@lucide/svelte";
  import type { PageData } from "./$types.js";

  const TRAFFIC_REFRESH_INTERVAL_MS = 30_000;
  const TRAFFIC_REFRESH_TIMEOUT_MS = 5_000;

  let { data }: { data: PageData } = $props();

  let traffic = $state<TrafficData | null>(untrack(() => data.traffic));
  let trafficRefresh: AbortController | null = null;
  let trafficGeneration = 0;

  $effect(() => {
    const loadedTraffic = data.traffic;
    trafficGeneration += 1;
    trafficRefresh?.abort();
    traffic = loadedTraffic;
  });

  async function refreshTraffic() {
    if (trafficRefresh) return;

    const controller = new AbortController();
    trafficRefresh = controller;
    const refreshGeneration = trafficGeneration;
    const timeout = window.setTimeout(() => controller.abort(), TRAFFIC_REFRESH_TIMEOUT_MS);

    try {
      const response = await fetch("/admin/analytics/summary", {
        headers: { accept: "application/json" },
        cache: "no-store",
        signal: controller.signal
      });
      if (response.redirected || response.status === 401) {
        traffic = null;
        await goto("/auth/login?redirectTo=%2Fadmin");
        return;
      }
      if (response.status === 403) {
        traffic = null;
        await goto("/");
        return;
      }
      if (!response.ok) return;

      const refreshedTraffic: unknown = await response.json();
      if (
        trafficRefresh === controller &&
        trafficGeneration === refreshGeneration &&
        isTrafficData(refreshedTraffic)
      ) {
        traffic = refreshedTraffic;
      }
    } catch {
      // Keep showing the most recently loaded aggregate if a refresh fails.
    } finally {
      window.clearTimeout(timeout);
      if (trafficRefresh === controller) {
        trafficRefresh = null;
      }
    }
  }

  onMount(() => {
    if (traffic === null) void refreshTraffic();

    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") void refreshTraffic();
    };
    const interval = window.setInterval(refreshWhenVisible, TRAFFIC_REFRESH_INTERVAL_MS);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
      trafficRefresh?.abort();
    };
  });

  const unavailable = (value: number | null) => value === null;
  const count = (value: number | null) => value?.toLocaleString("en-DK") ?? "—";

  let attentionItems = $derived([
    {
      label: "Inactive accounts",
      description: "Accounts that are currently unable to sign in.",
      value: data.metrics.users.attention,
      href: "/admin/users",
      icon: UserRoundX
    },
    {
      label: "Hidden recipes",
      description: "Recipes currently hidden from their regular audience.",
      value: data.metrics.recipes.attention,
      href: "/recipes",
      icon: BookOpen
    },
    {
      label: "Ingredients without barcodes",
      description: "Catalog items that were added without a product barcode.",
      value: data.metrics.ingredients.attention,
      href: "/admin/ingredients",
      icon: ScanBarcode
    },
    {
      label: "Sessions without players",
      description: "Game sessions that do not have any players yet.",
      value: data.metrics.sessions.attention,
      href: "/game",
      icon: Gamepad2
    }
  ]);
</script>

<div class="mx-auto max-w-7xl space-y-8">
  <AdminPageHeader
    title="Administration"
    description="Keep an eye on the catalog, accounts, and game data from one place."
  />

  <section aria-labelledby="overview-heading" class="space-y-4">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 id="overview-heading" class="mb-0 text-lg font-semibold">Overview</h2>
        <p class="text-muted-foreground text-sm">Live totals from the application database.</p>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card.Root>
        <Card.Header>
          <Card.Title>Users</Card.Title>
          <Card.Description>Registered accounts</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <Users class="size-5" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-3xl font-semibold tabular-nums">{count(data.metrics.users.total)}</p>
          {#if unavailable(data.metrics.users.total)}
            <p class="text-muted-foreground mt-1 text-xs">Temporarily unavailable</p>
          {/if}
        </Card.Content>
        <Card.Footer>
          <Button href="/admin/users" variant="ghost" size="sm" class="-ml-3">
            Manage users <ArrowRight />
          </Button>
        </Card.Footer>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Recipes</Card.Title>
          <Card.Description>Recipes in the collection</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <BookOpen class="size-5" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-3xl font-semibold tabular-nums">{count(data.metrics.recipes.total)}</p>
          {#if unavailable(data.metrics.recipes.total)}
            <p class="text-muted-foreground mt-1 text-xs">Temporarily unavailable</p>
          {/if}
        </Card.Content>
        <Card.Footer>
          <Button href="/recipes" variant="ghost" size="sm" class="-ml-3">
            Browse recipes <ArrowRight />
          </Button>
        </Card.Footer>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Ingredients</Card.Title>
          <Card.Description>Cataloged ingredients</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <ChefHat class="size-5" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-3xl font-semibold tabular-nums">{count(data.metrics.ingredients.total)}</p>
          {#if unavailable(data.metrics.ingredients.total)}
            <p class="text-muted-foreground mt-1 text-xs">Temporarily unavailable</p>
          {/if}
        </Card.Content>
        <Card.Footer>
          <Button href="/admin/ingredients" variant="ghost" size="sm" class="-ml-3">
            Manage ingredients <ArrowRight />
          </Button>
        </Card.Footer>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Game sessions</Card.Title>
          <Card.Description>Created game sessions</Card.Description>
          <Card.Action class="bg-primary/10 text-primary rounded-lg p-2">
            <Gamepad2 class="size-5" />
          </Card.Action>
        </Card.Header>
        <Card.Content>
          <p class="text-3xl font-semibold tabular-nums">{count(data.metrics.sessions.total)}</p>
          {#if unavailable(data.metrics.sessions.total)}
            <p class="text-muted-foreground mt-1 text-xs">Temporarily unavailable</p>
          {/if}
        </Card.Content>
        <Card.Footer>
          <Button href="/game" variant="ghost" size="sm" class="-ml-3">
            View sessions <ArrowRight />
          </Button>
        </Card.Footer>
      </Card.Root>
    </div>
  </section>

  <TrafficOverview {traffic} />

  <div class="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.65fr)]">
    <section aria-labelledby="attention-heading" class="space-y-4">
      <div>
        <h2 id="attention-heading" class="mb-0 text-lg font-semibold">Things to review</h2>
        <p class="text-muted-foreground text-sm">
          Useful catalog and account details that may need attention.
        </p>
      </div>

      <Card.Root>
        <Card.Content class="grid gap-1 p-0">
          {#each attentionItems as item}
            <a
              href={item.href}
              class="hover:bg-muted/60 focus-visible:ring-ring flex items-center gap-3 rounded-lg p-4 transition-colors focus-visible:ring-2 focus-visible:outline-none"
            >
              <span class="bg-muted text-muted-foreground rounded-lg p-2">
                <item.icon class="size-4" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block font-medium">{item.label}</span>
                <span class="text-muted-foreground block text-xs sm:text-sm">
                  {item.description}
                </span>
              </span>
              <span class="flex items-center gap-2">
                {#if item.value === null}
                  <CircleAlert class="text-muted-foreground size-4" aria-label="Unavailable" />
                  <span class="sr-only">Unavailable</span>
                {:else}
                  <span class="text-lg font-semibold tabular-nums">{item.value}</span>
                {/if}
                <ArrowRight class="text-muted-foreground size-4" />
              </span>
            </a>
          {/each}
        </Card.Content>
      </Card.Root>
    </section>

    <section aria-labelledby="manage-heading" class="space-y-4">
      <div>
        <h2 id="manage-heading" class="mb-0 text-lg font-semibold">Quick management</h2>
        <p class="text-muted-foreground text-sm">Jump directly to common admin tasks.</p>
      </div>

      <Card.Root>
        <Card.Content class="grid gap-2">
          <Button href="/admin/users" variant="outline" class="h-auto justify-start py-3">
            <Users />
            <span class="text-left">
              <span class="block">Users and permissions</span>
              <span class="text-muted-foreground block text-xs font-normal">Manage access</span>
            </span>
          </Button>
          <Button href="/admin/ingredients" variant="outline" class="h-auto justify-start py-3">
            <ScanBarcode />
            <span class="text-left">
              <span class="block">Ingredient catalog</span>
              <span class="text-muted-foreground block text-xs font-normal"
                >Add or scan products</span
              >
            </span>
          </Button>
          <Button href="/admin/game/drinks" variant="outline" class="h-auto justify-start py-3">
            <GlassWater />
            <span class="text-left">
              <span class="block">Game drinks</span>
              <span class="text-muted-foreground block text-xs font-normal"
                >Maintain drink options</span
              >
            </span>
          </Button>
        </Card.Content>
      </Card.Root>
    </section>
  </div>
</div>

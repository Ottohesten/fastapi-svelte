<script lang="ts">
  import "../app.css";
  import { afterNavigate } from "$app/navigation";
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import ChefHat from "@lucide/svelte/icons/chef-hat";
  import LogIn from "@lucide/svelte/icons/log-in";
  import LogOut from "@lucide/svelte/icons/log-out";
  import Menu from "@lucide/svelte/icons/menu";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import { Button, buttonVariants } from "$lib/components/ui/button";
  import * as Sheet from "$lib/components/ui/sheet";
  import {
    BROWSER_SESSION_STORAGE_KEY,
    buildPageMetrics,
    postPageMetrics
  } from "$lib/observability/page-metrics";
  import { hasBrowserTelemetryOptOut } from "$lib/observability/sentry-config";

  let { children, data } = $props();

  type NavItem = { href: string; label: string; requiredScopes?: string | string[] };

  const authenticatedLinks: NavItem[] = [
    { href: "/recipes", label: "Recipes", requiredScopes: "recipes:read" },
    { href: "/ingredients", label: "Ingredients", requiredScopes: "ingredients:read" },
    { href: "/game", label: "Games" }
  ];
  const anonymousLinks: NavItem[] = [
    { href: "/", label: "Home" },
    { href: "/game", label: "Game" }
  ];

  let mobileOpen = $state(false);

  const isAdmin = $derived(
    $page.url.pathname === "/admin" || $page.url.pathname.startsWith("/admin/")
  );
  const navigationLinks = $derived(
    data.authenticatedUser
      ? authenticatedLinks.filter((item) => hasRequiredScopes(item, data.scopes))
      : anonymousLinks
  );
  let initialPageViewRecorded = false;

  function hasRequiredScopes(item: NavItem, scopes: string[] | undefined) {
    if (!item.requiredScopes) return true;
    if (!scopes) return false;
    return Array.isArray(item.requiredScopes)
      ? item.requiredScopes.every((scope) => scopes.includes(scope))
      : scopes.includes(item.requiredScopes);
  }

  function isActive(href: string) {
    return $page.url.pathname === href || $page.url.pathname.startsWith(`${href}/`);
  }

  function recordPageView(routeId: string | null | undefined) {
    if (!routeId || hasBrowserTelemetryOptOut(navigator)) return;

    let browserSessionStarted = true;
    try {
      browserSessionStarted = sessionStorage.getItem(BROWSER_SESSION_STORAGE_KEY) === "1";
    } catch {
      // Some privacy modes disable session storage. Page views still remain useful.
    }

    const metrics = buildPageMetrics({
      routeId,
      browserSessionStarted
    });

    void postPageMetrics(metrics);

    if (!browserSessionStarted) {
      try {
        sessionStorage.setItem(BROWSER_SESSION_STORAGE_KEY, "1");
      } catch {
        // Do not make telemetry a dependency of navigation.
      }
    }
  }

  afterNavigate(({ to, type }) => {
    if (type === "enter") {
      if (initialPageViewRecorded) return;
      initialPageViewRecorded = true;
    }

    recordPageView(to?.route.id);
  });

  onMount(() => {
    document.body.setAttribute("data-svelte-hydrated", "true");

    // SvelteKit may finish its initial navigation before the afterNavigate callback is mounted.
    if (!initialPageViewRecorded) {
      initialPageViewRecorded = true;
      recordPageView($page.route.id);
    }
  });
</script>

{#if isAdmin}
  {@render children()}
{:else}
  <header
    class="border-border/70 bg-background/85 supports-[backdrop-filter]:bg-background/70 sticky top-0 z-40 border-b backdrop-blur-xl"
  >
    <div class="container flex h-16 items-center gap-3">
      <a
        href="/"
        class="text-foreground focus-visible:ring-ring flex min-w-0 items-center gap-2.5 rounded-lg font-semibold tracking-tight focus-visible:ring-2 focus-visible:outline-none"
      >
        <span
          class="bg-primary text-primary-foreground grid size-9 shrink-0 place-items-center rounded-xl shadow-sm"
        >
          <ChefHat class="size-5" />
        </span>
        <span class="truncate text-base sm:text-lg">Internationaleregler</span>
      </a>

      <nav aria-label="Primary navigation" class="ml-auto hidden items-center gap-1 md:flex">
        {#each navigationLinks as link (link.href)}
          <Button
            href={link.href}
            variant={isActive(link.href) ? "secondary" : "ghost"}
            size="sm"
            aria-current={isActive(link.href) ? "page" : undefined}
          >
            {link.label}
          </Button>
        {/each}
      </nav>

      <div class="ml-auto hidden items-center gap-1 md:flex">
        {#if data.authenticatedUser?.is_superuser}
          <Button href="/admin" variant="ghost" size="sm">
            <ShieldCheck />
            Admin
          </Button>
        {/if}
        <ThemeToggle />
        {#if data.authenticatedUser}
          <Button href="/auth/logout" variant="outline" size="sm">
            <LogOut />
            Logout
          </Button>
        {:else}
          <Button href="/auth/login" size="sm">
            <LogIn />
            Login
          </Button>
        {/if}
      </div>

      <Sheet.Root bind:open={mobileOpen}>
        <Sheet.Trigger
          class={buttonVariants({ variant: "ghost", size: "icon", class: "ml-auto md:hidden" })}
          aria-label="Open navigation"
          title="Open navigation"
        >
          <Menu class="size-5" />
        </Sheet.Trigger>
        <Sheet.Content
          side="left"
          class="flex w-[88vw] flex-col p-0 sm:max-w-sm"
          data-sveltekit-replacestate
        >
          <Sheet.Header class="border-border border-b px-5 py-5 pr-12 text-left">
            <Sheet.Title class="flex items-center gap-2.5">
              <span
                class="bg-primary text-primary-foreground grid size-9 place-items-center rounded-xl"
              >
                <ChefHat class="size-5" />
              </span>
              Internationaleregler
            </Sheet.Title>
            <Sheet.Description>Navigate the site and manage your account.</Sheet.Description>
          </Sheet.Header>

          <nav aria-label="Mobile navigation" class="flex flex-col gap-1 p-4">
            {#each navigationLinks as link (link.href)}
              <Button
                href={link.href}
                variant={isActive(link.href) ? "secondary" : "ghost"}
                class="h-12 w-full justify-start px-4 text-base"
                aria-current={isActive(link.href) ? "page" : undefined}
              >
                {link.label}
              </Button>
            {/each}
            {#if data.authenticatedUser?.is_superuser}
              <Button
                href="/admin"
                variant="ghost"
                class="h-12 w-full justify-start px-4 text-base"
              >
                <ShieldCheck />
                Admin
              </Button>
            {/if}
          </nav>

          <div class="border-border mt-auto space-y-4 border-t p-4">
            <div class="flex min-h-11 items-center justify-between gap-3 px-2">
              <div>
                <p class="text-sm font-medium">Appearance</p>
                <p class="text-muted-foreground text-xs">Light, dark, or system</p>
              </div>
              <ThemeToggle />
            </div>

            {#if data.authenticatedUser}
              <Button href="/auth/logout" variant="outline" class="h-11 w-full">
                <LogOut />
                Logout
              </Button>
            {:else}
              <Button href="/auth/login" class="h-11 w-full">
                <LogIn />
                Login
              </Button>
            {/if}
          </div>
        </Sheet.Content>
      </Sheet.Root>
    </div>
  </header>

  <main class="min-h-[calc(100svh-4rem)]">
    {@render children()}
  </main>
{/if}

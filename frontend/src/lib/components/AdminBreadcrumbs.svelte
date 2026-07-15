<script lang="ts">
  import { page } from "$app/stores";
  import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";

  const labels: Record<string, string> = {
    "/admin": "Overview",
    "/admin/users": "Users",
    "/admin/ingredients": "Ingredients",
    "/admin/game/drinks": "Drinks",
    "/admin/game/sessions": "Game sessions",
    "/admin/game/players": "Players"
  };

  const currentLabel = $derived(labels[$page.url.pathname] ?? "Administration");
  const isGamePage = $derived($page.url.pathname.startsWith("/admin/game/"));
</script>

<Breadcrumb.Root>
  <Breadcrumb.List>
    <Breadcrumb.Item class="hidden sm:flex">
      <Breadcrumb.Link href="/admin">Admin</Breadcrumb.Link>
    </Breadcrumb.Item>
    <Breadcrumb.Separator class="hidden sm:flex" />
    {#if isGamePage}
      <Breadcrumb.Item class="hidden sm:flex">
        <span>Game</span>
      </Breadcrumb.Item>
      <Breadcrumb.Separator class="hidden sm:flex" />
    {/if}
    <Breadcrumb.Item>
      <Breadcrumb.Page>{currentLabel}</Breadcrumb.Page>
    </Breadcrumb.Item>
  </Breadcrumb.List>
</Breadcrumb.Root>

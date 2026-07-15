<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import BookOpen from "@lucide/svelte/icons/book-open";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import CookingPot from "@lucide/svelte/icons/cooking-pot";
  import CupSoda from "@lucide/svelte/icons/cup-soda";
  import Gamepad2 from "@lucide/svelte/icons/gamepad-2";
  import House from "@lucide/svelte/icons/house";
  import LayoutDashboard from "@lucide/svelte/icons/layout-dashboard";
  import LogOut from "@lucide/svelte/icons/log-out";
  import Salad from "@lucide/svelte/icons/salad";
  import Users from "@lucide/svelte/icons/users";

  type SidebarUser = {
    email: string;
    full_name?: string | null;
  } | null;

  let { user = null }: { user?: SidebarUser } = $props();

  const sidebar = Sidebar.useSidebar();

  const adminItems = [
    { title: "Overview", url: "/admin", icon: LayoutDashboard, exact: true },
    { title: "Users", url: "/admin/users", icon: Users },
    { title: "Ingredients", url: "/admin/ingredients", icon: Salad },
    { title: "Drinks", url: "/admin/game/drinks", icon: CupSoda }
  ];

  const applicationItems = [
    { title: "Recipe library", url: "/recipes", icon: BookOpen },
    { title: "Game sessions", url: "/game", icon: Gamepad2 },
    { title: "Home", url: "/", icon: House, exact: true }
  ];

  const displayName = $derived(user?.full_name?.trim() || "Administrator");
  const initials = $derived(
    displayName
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "A"
  );

  function isActive(item: { url: string; exact?: boolean }) {
    return item.exact
      ? page.url.pathname === item.url
      : page.url.pathname === item.url || page.url.pathname.startsWith(`${item.url}/`);
  }

  async function navigate(url: string) {
    await goto(url, { replaceState: sidebar.isMobile && sidebar.openMobile });
  }
</script>

{#snippet adminOverviewTooltip()}
  Admin overview
{/snippet}

{#snippet userTooltip()}
  {displayName}
{/snippet}

<Sidebar.Root variant="inset" collapsible="icon">
  <Sidebar.Header class="border-sidebar-border border-b p-2">
    <Sidebar.Menu>
      <Sidebar.MenuItem>
        <Sidebar.MenuButton size="lg" tooltipContent={adminOverviewTooltip}>
          {#snippet child({ props })}
            <a href="/admin" {...props}>
              <span
                class="bg-sidebar-primary text-sidebar-primary-foreground flex size-8 shrink-0 items-center justify-center rounded-lg shadow-sm"
              >
                <CookingPot class="size-4" />
              </span>
              <span class="grid min-w-0 flex-1 text-left leading-tight">
                <span class="truncate font-semibold">Internationaleregler</span>
                <span class="text-sidebar-foreground/65 truncate text-xs">Administration</span>
              </span>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Header>

  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.GroupLabel>Manage</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each adminItems as item (item.url)}
            {#snippet itemTooltip()}
              {item.title}
            {/snippet}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton isActive={isActive(item)} tooltipContent={itemTooltip}>
                {#snippet child({ props })}
                  <a href={item.url} {...props}>
                    <item.icon />
                    <span>{item.title}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <Sidebar.Separator />

    <Sidebar.Group>
      <Sidebar.GroupLabel>Application</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each applicationItems as item (item.url)}
            {#snippet itemTooltip()}
              {item.title}
            {/snippet}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton tooltipContent={itemTooltip}>
                {#snippet child({ props })}
                  <a href={item.url} {...props}>
                    <item.icon />
                    <span>{item.title}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer class="border-sidebar-border gap-2 border-t p-2">
    <div
      class="flex items-center justify-between gap-2 px-2 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0"
    >
      <span class="text-sidebar-foreground/65 text-xs group-data-[collapsible=icon]:hidden"
        >Appearance</span
      >
      <ThemeToggle />
    </div>

    <Sidebar.Menu>
      <Sidebar.MenuItem>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            {#snippet child({ props })}
              <Sidebar.MenuButton
                {...props}
                size="lg"
                class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                tooltipContent={userTooltip}
              >
                <Avatar.Root class="size-8 rounded-lg">
                  <Avatar.Fallback class="bg-sidebar-accent rounded-lg font-semibold">
                    {initials}
                  </Avatar.Fallback>
                </Avatar.Root>
                <span class="grid min-w-0 flex-1 text-left leading-tight">
                  <span class="truncate text-sm font-medium">{displayName}</span>
                  <span class="text-sidebar-foreground/65 truncate text-xs">{user?.email}</span>
                </span>
                <ChevronUp class="ml-auto size-4" />
              </Sidebar.MenuButton>
            {/snippet}
          </DropdownMenu.Trigger>
          <DropdownMenu.Content
            side={sidebar.isMobile ? "bottom" : "right"}
            align="end"
            class="min-w-56"
          >
            <DropdownMenu.Label>
              <span class="block truncate font-medium">{displayName}</span>
              <span class="text-muted-foreground block truncate text-xs font-normal"
                >{user?.email}</span
              >
            </DropdownMenu.Label>
            <DropdownMenu.Separator />
            <DropdownMenu.Item onclick={() => navigate("/")}>
              <House />
              Back to site
            </DropdownMenu.Item>
            <DropdownMenu.Item variant="destructive" onclick={() => navigate("/auth/logout")}>
              <LogOut />
              Log out
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Footer>
  <Sidebar.Rail />
</Sidebar.Root>

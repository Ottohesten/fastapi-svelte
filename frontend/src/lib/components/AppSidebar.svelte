<script lang="ts">
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { Collapsible } from "bits-ui";
  // import { Calendar } from 'bits-ui';
  import Calendar from "lucide-svelte/icons/calendar";
  import ChefHat from "lucide-svelte/icons/chef-hat";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import House from "lucide-svelte/icons/house";
  import Inbox from "lucide-svelte/icons/inbox";
  import Search from "lucide-svelte/icons/search";
  import Settings from "lucide-svelte/icons/settings";
  import User from "lucide-svelte/icons/user";
  import UtensilsCrossed from "lucide-svelte/icons/utensils-crossed";
  import BookOpen from "lucide-svelte/icons/book-open";

  const items = [
    // {
    // 	title: 'Home',
    // 	url: '/',
    // 	icon: House
    // },
    {
      title: "Users",
      url: "/admin/users",
      icon: User
    },
    {
      title: "Game",
      url: "#",
      icon: Inbox,
      collapsible: true,
      // submenus
      children: [
        {
          title: "Sessions",
          url: "/admin/game/sessions",
          icon: Inbox
        },
        {
          title: "Drinks",
          url: "/admin/game/drinks",
          icon: Inbox
        },
        {
          title: "Players",
          url: "/admin/game/players",
          icon: Calendar
        }
      ]
    },
    {
      title: "Kitchen",
      url: "#",
      icon: ChefHat,
      collapsible: true,
      // submenus
      children: [
        {
          title: "Ingredients",
          url: "/admin/ingredients",
          icon: UtensilsCrossed
        },
        {
          title: "Recipes",
          url: "/admin/recipes",
          icon: BookOpen
        }
      ]
    },
    {
      title: "Calendar",
      url: "#",
      icon: Calendar
      // children: [
      // 	{
      // 		title: 'test 1',
      // 		url: '#',
      // 		icon: Inbox
      // 	},
      // 	{
      // 		title: 'Test 2',
      // 		url: '/',
      // 		icon: Calendar
      // 	}
      // ]
    },
    {
      title: "Search",
      url: "#",
      icon: Search
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings
    }
  ];
</script>

<Sidebar.Root collapsible="offcanvas" class="">
  <!-- <Sidebar.Inset class="inset-y-10"> -->
  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.GroupLabel>Application</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each items as item (item.title)}
            <Collapsible.Root class="group/collapsible">
              <Sidebar.MenuItem>
                {#if item.collapsible}
                  <Collapsible.Trigger class="w-full">
                    {#snippet child({ props })}
                      <Sidebar.MenuButton {...props}>
                        <item.icon />
                        <span>{item.title}</span>
                        <ChevronDown
                          class="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180"
                        />
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                {:else}
                  <Sidebar.MenuButton>
                    {#snippet child({ props })}
                      <a href={item.url} {...props}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    {/snippet}
                  </Sidebar.MenuButton>
                {/if}
                <Collapsible.Content>
                  {#if item.children}
                    <Sidebar.MenuSub>
                      {#each item.children as subItem (subItem.title)}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton>
                            {#snippet child({ props })}
                              <a href={subItem.url} {...props}>
                                <subItem.icon />
                                <span>{subItem.title}</span>
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  {/if}
                </Collapsible.Content>
              </Sidebar.MenuItem>
            </Collapsible.Root>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
      <!-- <Sidebar.Rail /> -->
    </Sidebar.Group>
  </Sidebar.Content>
  <!-- </Sidebar.Inset> -->
</Sidebar.Root>

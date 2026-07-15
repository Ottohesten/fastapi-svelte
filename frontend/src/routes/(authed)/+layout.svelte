<script lang="ts">
  import AdminBreadcrumbs from "$lib/components/AdminBreadcrumbs.svelte";
  import AppSidebar from "$lib/components/AppSidebar.svelte";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";

  let { children, data } = $props();
</script>

<Sidebar.Provider style="--sidebar-width: 17rem; --sidebar-width-icon: 3rem;">
  <AppSidebar user={data.authenticatedUser} />
  <Sidebar.Inset>
    <header
      class="border-border/70 bg-background/90 supports-backdrop-filter:bg-background/75 sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b px-4 backdrop-blur"
    >
      <Sidebar.Trigger class="-ml-1 size-8" />
      <Separator orientation="vertical" class="mr-1 h-4" />
      <AdminBreadcrumbs />
      <a
        href="/"
        class="text-muted-foreground hover:text-foreground ml-auto hidden text-xs font-medium transition-colors sm:block"
      >
        View site
      </a>
    </header>

    <div class="flex flex-1 flex-col p-4 sm:p-6 lg:p-8">
      <div class="mx-auto w-full max-w-[96rem]">
        {@render children?.()}
      </div>
    </div>
  </Sidebar.Inset>
</Sidebar.Provider>

<script lang="ts">
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import AppSidebar from "$lib/components/AppSidebar.svelte";
  import { Trigger as SidebarTrigger } from "$lib/components/ui/sidebar/index.js";
  import SidebarSwipeGesture from "$lib/components/ui/sidebar/sidebar-swipe-gesture.svelte";

  let { children } = $props();
</script>

<!-- <div class="flex h-screen"> -->
<div class="flex min-h-screen">
  <Sidebar.Provider>
    <SidebarSwipeGesture />
    <AppSidebar />
    <main class="w-full">
      <!-- Mobile Top Bar -->
      <div
        class="sticky top-0 z-0 flex items-center gap-2 border-b border-gray-200 bg-white/80 p-3 backdrop-blur supports-backdrop-filter:bg-white/60 md:hidden dark:border-gray-800 dark:bg-gray-900/60"
      >
        <SidebarTrigger class="h-9 w-9" />
        <span class="text-sm font-medium text-gray-700 dark:text-gray-200">Admin</span>
      </div>

      <div class="p-3 md:p-4 lg:p-6">
        {@render children?.()}
      </div>
    </main>
  </Sidebar.Provider>
</div>
1

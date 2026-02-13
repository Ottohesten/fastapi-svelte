<script lang="ts">
  let { data } = $props();

  // Placeholder stats — replace with real data from loaders/endpoints later
  let stats = {
    users: "—",
    games: "—",
    recipes: "—"
  };
</script>

<main class="p-6">
  <header class="mb-6">
    <h1 class="text-3xl font-semibold">Administration</h1>
    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
      Welcome to the admin dashboard. Use these tools to manage users, game data, content, and site
      settings.
    </p>
  </header>

  <section class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
    <div
      class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm md:col-span-2 dark:border-gray-800 dark:bg-gray-900/50 dark:shadow-none"
    >
      <h2 class="mb-3 text-lg font-medium">Overview</h2>
      <div class="flex gap-4">
        <div class="flex-1 rounded bg-gray-50 p-4 dark:bg-gray-900/30">
          <div class="text-xs text-gray-500">Users</div>
          <div class="text-2xl font-bold">{stats.users}</div>
        </div>
        <div class="flex-1 rounded bg-gray-50 p-4 dark:bg-gray-900/30">
          <div class="text-xs text-gray-500">Game Sessions</div>
          <div class="text-2xl font-bold">{stats.games}</div>
        </div>
        <div class="flex-1 rounded bg-gray-50 p-4 dark:bg-gray-900/30">
          <div class="text-xs text-gray-500">Recipes</div>
          <div class="text-2xl font-bold">{stats.recipes}</div>
        </div>
      </div>

      <div class="mt-4 text-sm text-gray-600">
        This page is a centralized place for administrative actions. Connect real metrics by
        returning values from this page's loader.
      </div>
    </div>

    <aside
      class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/50 dark:shadow-none"
    >
      <h3 class="text-md mb-3 font-medium">Quick Actions</h3>
      <div class="flex flex-col gap-2">
        <a
          href="/admin/users"
          class="block rounded bg-sky-500 px-3 py-2 text-left text-white hover:bg-sky-600"
          >Manage Users</a
        >
        <a
          href="/admin/roles"
          class="block rounded border border-gray-600 px-3 py-2 text-left text-gray-100 hover:bg-gray-700"
          >Manage Roles</a
        >
        <a
          href="/admin/game"
          class="block rounded border border-gray-600 px-3 py-2 text-left text-gray-100 hover:bg-gray-700"
          >Game Data</a
        >
        <a
          href="/admin/recipes"
          class="block rounded border border-gray-600 px-3 py-2 text-left text-gray-100 hover:bg-gray-700"
          >Recipes & Ingredients</a
        >
      </div>
    </aside>
  </section>

  <section class="grid grid-cols-1 gap-4 md:grid-cols-2">
    <div
      class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/50 dark:shadow-none"
    >
      <h3 class="text-md mb-2 font-medium">Helpful Tips</h3>
      <ul class="ml-5 list-disc text-sm text-gray-300">
        <li>Use the dedicated endpoints to seed or import initial game data.</li>
        <li>Review user activity before changing roles or permissions.</li>
        <li>Back up important data before running destructive operations.</li>
      </ul>
    </div>

    <div
      class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900/50 dark:shadow-none"
    >
      <h3 class="text-md mb-2 font-medium">Recent Activity</h3>
      <div class="text-sm text-gray-300">
        No recent activity to show. Add an activity feed or audit logs endpoint and render items
        here.
      </div>
    </div>
  </section>
</main>

<script lang="ts">
  import { enhance } from "$app/forms";
  import type { components } from "$lib/api/v1";
  import { Trash, Trash2 } from "lucide-svelte";

  type Props = {
    session: components["schemas"]["GameSessionPublic"];
    authenticatedUser?: components["schemas"]["UserMePublic"];
  };

  let { session, authenticatedUser }: Props = $props();

  const canDelete = $derived.by(
    () =>
      !!authenticatedUser &&
      (authenticatedUser.id === session.owner.id ||
        authenticatedUser.scopes?.includes("games:delete"))
  );

  function formatCreated(dateStr: string): string {
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return dateStr;
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yy = String(d.getFullYear()).slice(-2);
    const hh = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${dd}/${mm}/${yy}, ${hh}:${min}`;
  }
</script>

<div
  class="my-4 rounded-xl border border-gray-300 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900/40"
>
  <a
    href="/game/{session.id}"
    aria-label={"Open game session “" + session.title + "”"}
    class="group block rounded-xl p-5 transition-all hover:-translate-y-0.5 hover:shadow-md focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
  >
    <div class="flex items-start gap-4">
      <div class="flex-1">
        <div class="mb-1 flex items-center justify-between gap-3">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {session.title}
          </h2>
          <svg
            class="h-5 w-5 text-gray-400 transition-transform group-hover:translate-x-0.5 dark:text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </div>
        <div class="mb-3 flex flex-col gap-1 text-sm text-gray-600 dark:text-gray-400">
          <span class="inline-flex items-center gap-1">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <span class="truncate">{session.owner.full_name ?? session.owner.email}</span>
          </span>
          <span class="text-xs text-gray-500 dark:text-gray-400">
            Created: <time datetime={session.created_at}>{formatCreated(session.created_at)}</time>
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span
            class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            {session.players.length} players
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 7l9-4 9 4-9 4-9-4zm0 6l9 4 9-4M3 7v6m18-6v6"
              />
            </svg>
            {session.teams.length} teams
          </span>
        </div>
      </div>
    </div>
  </a>

  {#if canDelete}
    <div
      class="border-t border-gray-100 bg-gray-50 px-5 py-3 dark:border-gray-800 dark:bg-gray-900/40"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Session Actions</span>
        <form action="/game?/deleteGame" method="POST" use:enhance class="inline">
          <input type="hidden" name="game_session_id" value={session.id} />
          <button
            type="submit"
            class="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:border-red-300 hover:bg-red-100 focus:ring-2 focus:ring-red-500 focus:ring-offset-1 focus:outline-none dark:border-red-900/50 dark:bg-red-900/40 dark:text-red-300 dark:hover:border-red-800 dark:hover:bg-red-900/50"
            onclick={(e) => {
              if (
                !confirm(
                  "Are you sure you want to delete this game session? This action cannot be undone."
                )
              ) {
                e.preventDefault();
              }
            }}
          >
            <!-- <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg> -->
            <Trash2 class="h-3 w-3" />
            Delete
          </button>
        </form>
      </div>
    </div>
  {/if}
</div>

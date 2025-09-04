<script lang="ts">
	import type { components } from '$lib/api/v1';
	type Props = {
		session: components['schemas']['GameSessionPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};
	let { session, authenticatedUser }: Props = $props();
</script>

<a
	href="/game/{session.id}"
	aria-label={'Open game session “' + session.title + '”'}
	class="group my-4 block rounded-xl border border-gray-300 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-900/40"
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
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</div>
			<div class="mb-3 text-sm text-gray-600 dark:text-gray-400">
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

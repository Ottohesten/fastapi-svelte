<script lang="ts">
	import '../app.css';
	import Footer from '$lib/components/Footer.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { page } from '$app/stores';

	let { children, data } = $props();

	const linksAuth = [
		{ href: '/tiptap', label: 'Tiptap' },
		{ href: '/recipes', label: 'Recipes' },
		{ href: '/ingredients', label: 'Ingredients' },
		{ href: '/game', label: 'Game' }
	];

	const linksAnon = [{ href: '/', label: 'Home' }];

	const isActive = (href: string) =>
		$page.url.pathname === href || $page.url.pathname.startsWith(href + '/');
</script>

<header
	class="sticky top-0 z-30 border-b border-gray-200 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/50 dark:border-gray-800 dark:bg-gray-900/60"
>
	<div class="container flex h-16 items-center justify-between">
		<!-- Brand -->
		<a href="/" class="flex items-center gap-2 text-gray-900 no-underline dark:text-white">
			<svg class="h-6 w-6 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M3 7h18M5 7l1 12a2 2 0 002 2h8a2 2 0 002-2l1-12M8 7V5a4 4 0 118 0v2"
				/>
			</svg>
			<span class="text-lg font-semibold tracking-tight">FastAPI Svelte</span>
		</a>

		<!-- Nav links -->
		<nav class="hidden gap-1 md:flex">
			{#each data.authenticatedUser ? linksAuth : linksAnon as link}
				<a
					href={link.href}
					class="rounded-md px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 data-[active=true]:bg-gray-900 data-[active=true]:text-white dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
					data-active={isActive(link.href)}>{link.label}</a
				>
			{/each}
		</nav>

		<!-- Right actions -->
		<div class="flex items-center gap-2">
			<a
				href="/admin"
				class="hidden rounded-md px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 md:inline dark:text-gray-300 dark:hover:bg-gray-800"
				>Admin</a
			>
			<ThemeToggle />
			{#if !data.authenticatedUser}
				<a
					href="/auth/login"
					class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
					>Login</a
				>
			{:else}
				<a
					href="/auth/logout"
					class="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
					>Logout</a
				>
			{/if}
		</div>
	</div>
</header>

<main class="min-h-[calc(100vh-4rem)]">
	{@render children()}
</main>

<Footer />

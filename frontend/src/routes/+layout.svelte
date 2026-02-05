<script lang="ts">
	import "../app.css";
	import ThemeToggle from "$lib/components/ThemeToggle.svelte";
	import { page } from "$app/stores";
	import { slide } from "svelte/transition";

	let { children, data } = $props();

	// Mobile nav state
	let mobileOpen = $state(false);

	type NavItem = { href: string; label: string; requiredScopes?: string | string[] };
	const linksAuthConfig: NavItem[] = [
		// { href: '/tiptap', label: 'Tiptap' },
		{ href: "/recipes", label: "Recipes", requiredScopes: "recipes:read" },
		{ href: "/ingredients", label: "Ingredients", requiredScopes: "ingredients:read" },
		{ href: "/game", label: "Game" } // no scope required
	];

	function hasRequiredScopes(item: NavItem, scopes: string[] | undefined) {
		if (!item.requiredScopes) return true;
		if (!scopes) return false;
		return Array.isArray(item.requiredScopes)
			? item.requiredScopes.every((s) => scopes.includes(s))
			: scopes.includes(item.requiredScopes);
	}

	// Reactive filtered auth links based on current scopes
	const linksAuth: NavItem[] = $derived(
		linksAuthConfig.filter((i) => hasRequiredScopes(i, data.scopes))
	);

	const linksAnon = [
		{ href: "/", label: "Home" },
		{ href: "/game", label: "Game" }
	];

	const isActive = (href: string) =>
		$page.url.pathname === href || $page.url.pathname.startsWith(href + "/");
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
			<span class="max-w-[55vw] truncate text-lg font-semibold tracking-tight md:max-w-none"
				>Internationaleregler</span
			>
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
			<div class="hidden md:block"><ThemeToggle /></div>

			<!-- Desktop auth actions -->
			{#if !data.authenticatedUser}
				<a
					href="/auth/login"
					class="hidden rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 md:inline dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
					>Login</a
				>
			{:else}
				<a
					href="/auth/logout"
					class="hidden rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-emerald-700 md:inline"
					>Logout</a
				>
			{/if}

			<!-- Mobile menu toggle -->
			<button
				type="button"
				class="inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:bg-gray-100 focus:ring-2 focus:ring-blue-500 focus:outline-none md:hidden dark:text-gray-300 dark:hover:bg-gray-800"
				aria-label="Toggle menu"
				aria-expanded={mobileOpen}
				onclick={() => (mobileOpen = !mobileOpen)}
			>
				<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			</button>
		</div>
	</div>
</header>

<!-- Mobile menu panel -->
{#if mobileOpen}
	<div
		in:slide={{ duration: 180 }}
		out:slide={{ duration: 140 }}
		class="border-b border-gray-200 bg-white/95 backdrop-blur md:hidden dark:border-gray-800 dark:bg-gray-900/95"
	>
		<div class="container py-3">
			<nav class="flex flex-col gap-1">
				{#each data.authenticatedUser ? linksAuth : linksAnon as link}
					<a
						href={link.href}
						class="rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
						onclick={() => (mobileOpen = false)}>{link.label}</a
					>
				{/each}
				{#if data.authenticatedUser}
					<a
						href="/admin"
						class="rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
						onclick={() => (mobileOpen = false)}>Admin</a
					>
				{/if}
				<div class="my-2 h-px bg-gray-200 dark:bg-gray-800"></div>
				<div class="flex items-center justify-between px-1">
					<span class="text-sm text-gray-600 dark:text-gray-300">Theme</span>
					<ThemeToggle />
				</div>
				<div class="mt-2 flex items-center gap-2 px-1">
					{#if !data.authenticatedUser}
						<a
							href="/auth/login"
							class="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-center text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
							onclick={() => (mobileOpen = false)}>Login</a
						>
					{:else}
						<a
							href="/auth/logout"
							class="flex-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-center text-sm font-medium text-white hover:bg-emerald-700"
							onclick={() => (mobileOpen = false)}>Logout</a
						>
					{/if}
				</div>
			</nav>
		</div>
	</div>
{/if}

<main class="min-h-[calc(100vh-4rem)]">
	{@render children()}
</main>

<!-- <Footer /> -->

<script lang="ts">
	const year = new Date().getFullYear();
</script>

<footer
	class="border-t border-gray-200 bg-white/70 py-8 text-sm text-gray-600 backdrop-blur supports-[backdrop-filter]:bg-white/50 dark:border-gray-800 dark:bg-gray-900/60 dark:text-gray-300"
>
	<div class="container grid gap-6 md:grid-cols-3">
		<div>
			<div class="mb-2 flex items-center gap-2">
				<svg class="h-5 w-5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 7h18M5 7l1 12a2 2 0 002 2h8a2 2 0 002-2l1-12M8 7V5a4 4 0 118 0v2"
					/>
				</svg>
				<span class="font-semibold text-gray-900 dark:text-white">FastAPI Svelte</span>
			</div>
			<p class="max-w-md text-gray-600 dark:text-gray-400">
				A modern FastAPI + SvelteKit starter with Tailwind CSS, auth, and a growing set of UI
				components.
			</p>
		</div>
		<div class="grid grid-cols-2 gap-6 md:grid-cols-3">
			<div>
				<h4 class="mb-2 text-xs font-semibold tracking-wide text-gray-500 uppercase">Product</h4>
				<ul class="space-y-1">
					<li><a class="hover:underline" href="/recipes">Recipes</a></li>
					<li><a class="hover:underline" href="/ingredients">Ingredients</a></li>
					<li><a class="hover:underline" href="/game">Game</a></li>
				</ul>
			</div>
			<div>
				<h4 class="mb-2 text-xs font-semibold tracking-wide text-gray-500 uppercase">Resources</h4>
				<ul class="space-y-1">
					<li><a class="hover:underline" href="/blog">Blog</a></li>
					<li><a class="hover:underline" href="/tiptap">Editor</a></li>
					<li><a class="hover:underline" href="/">Docs</a></li>
				</ul>
			</div>
			<div>
				<h4 class="mb-2 text-xs font-semibold tracking-wide text-gray-500 uppercase">Account</h4>
				<ul class="space-y-1">
					<li><a class="hover:underline" href="/auth/login">Login</a></li>
					<li><a class="hover:underline" href="/auth/logout">Logout</a></li>
					<li><a class="hover:underline" href="/admin">Admin</a></li>
				</ul>
			</div>
		</div>
		<div class="flex items-end justify-between md:col-span-3">
			<p>© {year} FastAPI Svelte. All rights reserved.</p>
			<a
				class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
				href="https://github.com/Ottohesten/fastapi-svelte"
				target="_blank"
				rel="noreferrer">GitHub</a
			>
		</div>
	</div>
</footer>

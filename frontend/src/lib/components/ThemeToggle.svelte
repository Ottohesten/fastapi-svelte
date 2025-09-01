<script lang="ts">
	import { onMount } from 'svelte';
	const getPref = () => localStorage.getItem('theme');
	const setPref = (v: 'light' | 'dark' | 'system') => localStorage.setItem('theme', v);

	let theme: 'light' | 'dark' | 'system' = 'system';
	let systemMedia: MediaQueryList | null = null;
	let systemListener: ((e: MediaQueryListEvent) => void) | null = null;

	function ensureSystemMedia() {
		if (!systemMedia) systemMedia = window.matchMedia('(prefers-color-scheme: dark)');
		return systemMedia;
	}

	function apply(t: 'light' | 'dark' | 'system') {
		const media = ensureSystemMedia();
		const shouldDark = t === 'dark' || (t === 'system' && media.matches);
		document.documentElement.classList.toggle('dark', shouldDark);

		// Manage listener: attach only in system mode; detach otherwise
		if (t === 'system') {
			if (!systemListener) {
				systemListener = (e: MediaQueryListEvent) => {
					document.documentElement.classList.toggle('dark', e.matches);
				};
				media.addEventListener('change', systemListener);
			}
		} else if (systemListener) {
			media.removeEventListener('change', systemListener);
			systemListener = null;
		}
	}

	onMount(() => {
		const saved = getPref();
		if (saved === 'light' || saved === 'dark' || saved === 'system') theme = saved;
		apply(theme);
	});
</script>

<label class="sr-only" for="theme-select">Theme</label>
<select
	id="theme-select"
	bind:value={theme}
	aria-label="Theme"
	class="inline-flex items-center rounded-md border border-gray-300 bg-white/70 px-2.5 py-1.5 text-sm text-gray-700 shadow-sm backdrop-blur transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800/60 dark:text-gray-200 dark:hover:bg-gray-800"
	onchange={(e) => {
		const v = (e.target as HTMLSelectElement).value as 'light' | 'dark' | 'system';
		theme = v;
		setPref(theme);
		apply(theme);
	}}
>
	<option value="light">Light</option>
	<option value="dark">Dark</option>
	<option value="system">System</option>
</select>

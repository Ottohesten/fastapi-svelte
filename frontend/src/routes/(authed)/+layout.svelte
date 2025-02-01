<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/AppSidebar.svelte';

	let { children } = $props();
</script>

<!-- <div class="flex h-screen"> -->
<div class="flex">
	<Sidebar.Provider>
		<AppSidebar />
		<main class="w-full">
			<!-- <Sidebar.Trigger /> -->
			<div class="m-4">
				{@render children?.()}
			</div>
		</main>
	</Sidebar.Provider>
</div>
1

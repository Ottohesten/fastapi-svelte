<script lang="ts">
	import type { WithElementRef } from 'bits-ui';
	import type { HTMLSelectAttributes } from 'svelte/elements';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		value = $bindable(),
		class: className,
		children,
		...rest
	}: WithElementRef<HTMLSelectAttributes> = $props();
</script>

<select
	bind:this={ref}
	bind:value
	class={cn(
		'border-input bg-background ring-offset-background focus-visible:ring-ring h-10 w-full cursor-pointer rounded-md border px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:[color-scheme:dark]',
		className
	)}
	{...rest}
>
	{@render children?.()}
</select>

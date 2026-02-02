<script lang="ts">
	import CheckIcon from "@lucide/svelte/icons/check";
	import ChevronsUpDownIcon from "@lucide/svelte/icons/chevrons-up-down";
	import { tick } from "svelte";
	import * as Command from "$lib/components/ui/command/index.js";
	import * as Popover from "$lib/components/ui/popover/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { cn } from "$lib/utils.js";

	export interface ComboboxItem {
		value: string;
		label: string;
		disabled?: boolean;
		meta?: any;
	}
	interface Props {
		items: ComboboxItem[];
		value?: string; // bound
		placeholder?: string;
		searchPlaceholder?: string;
		emptyMessage?: string;
		ariaLabel?: string;
		class?: string;
		onSelect?: (item: ComboboxItem | null) => void;
		buttonClass?: string;
		popoverClass?: string;
		disabled?: boolean;
	}

	let {
		items = [],
		value = $bindable(""),
		placeholder = "Select...",
		searchPlaceholder = "Search...",
		emptyMessage = "No results.",
		ariaLabel = "Combobox",
		class: className = "",
		onSelect,
		buttonClass = "w-[200px] justify-between",
		popoverClass = "w-[240px]",
		disabled = false
	}: Props = $props();

	let open = $state(false);
	let triggerRef = $state<HTMLButtonElement>(null!);
	const selectedLabel = $derived(items.find((i) => i.value === value)?.label || "");

	function select(val: string) {
		if (val === value) {
			// toggle deselect? decide to keep selection; no-op
		} else {
			value = val;
		}
		const item = items.find((i) => i.value === value) || null;
		onSelect?.(item);
		closeAndFocusTrigger();
	}

	function closeAndFocusTrigger() {
		open = false;
		tick().then(() => triggerRef?.focus());
	}

	// No manual filter state; rely on Command's built-in filtering.
</script>

<div class={className} data-combobox>
	<Popover.Root bind:open>
		<Popover.Trigger bind:ref={triggerRef}>
			{#snippet child({ props })}
				<Button
					{...props}
					variant="outline"
					class={cn(buttonClass, "relative", !selectedLabel && "text-muted-foreground")}
					role="combobox"
					aria-expanded={open}
					aria-label={ariaLabel}
					{disabled}
				>
					{selectedLabel || placeholder}
					<ChevronsUpDownIcon class="opacity-50" />
				</Button>
			{/snippet}
		</Popover.Trigger>
		<Popover.Content class={cn(popoverClass, "p-0")} align="start">
			<Command.Root>
				<Command.Input placeholder={searchPlaceholder} />
				<Command.List>
					<Command.Empty>{emptyMessage}</Command.Empty>
					<Command.Group value="items">
						{#each items as item (item.value)}
							<Command.Item
								value={item.label}
								data-value={item.value}
								disabled={item.disabled}
								onSelect={() => select(item.value)}
							>
								<CheckIcon class={cn("mr-2 h-4 w-4", value !== item.value && "text-transparent")} />
								{item.label}
							</Command.Item>
						{/each}
					</Command.Group>
				</Command.List>
			</Command.Root>
		</Popover.Content>
	</Popover.Root>
</div>

<style>
	/* Styling hook placeholder; extend as needed */
</style>

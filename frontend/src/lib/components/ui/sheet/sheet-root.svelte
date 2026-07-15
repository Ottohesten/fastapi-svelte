<script lang="ts">
  import { Dialog as SheetPrimitive } from "bits-ui";
  import { useShallowOverlay } from "$lib/navigation/shallow-overlay.svelte.js";

  let {
    open = $bindable(false),
    onOpenChange,
    shallowRouting = true,
    ...restProps
  }: SheetPrimitive.RootProps & { shallowRouting?: boolean } = $props();

  function setOpen(value: boolean) {
    if (open === value) return;
    open = value;
    onOpenChange?.(value);
  }

  const componentId = $props.id();
  const overlay = useShallowOverlay({
    id: `sheet-${componentId}`,
    getOpen: () => open,
    setOpen,
    getEnabled: () => shallowRouting
  });
</script>

<SheetPrimitive.Root {open} onOpenChange={overlay.handleOpenChange} {...restProps} />

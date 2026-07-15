<script lang="ts">
  import { Dialog as DialogPrimitive } from "bits-ui";
  import { useShallowOverlay } from "$lib/navigation/shallow-overlay.svelte.js";

  let {
    open = $bindable(false),
    onOpenChange,
    shallowRouting = true,
    ...restProps
  }: DialogPrimitive.RootProps & { shallowRouting?: boolean } = $props();

  function setOpen(value: boolean) {
    if (open === value) return;
    open = value;
    onOpenChange?.(value);
  }

  const componentId = $props.id();
  const overlay = useShallowOverlay({
    id: `dialog-${componentId}`,
    getOpen: () => open,
    setOpen,
    getEnabled: () => shallowRouting
  });
</script>

<DialogPrimitive.Root {open} onOpenChange={overlay.handleOpenChange} {...restProps} />

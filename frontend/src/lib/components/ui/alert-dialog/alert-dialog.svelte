<script lang="ts">
  import { AlertDialog as AlertDialogPrimitive } from "bits-ui";
  import { useShallowOverlay } from "$lib/navigation/shallow-overlay.svelte.js";

  let {
    open = $bindable(false),
    onOpenChange,
    shallowRouting = true,
    ...restProps
  }: AlertDialogPrimitive.RootProps & { shallowRouting?: boolean } = $props();

  function setOpen(value: boolean) {
    if (open === value) return;
    open = value;
    onOpenChange?.(value);
  }

  const componentId = $props.id();
  const overlay = useShallowOverlay({
    id: `alert-dialog-${componentId}`,
    getOpen: () => open,
    setOpen,
    getEnabled: () => shallowRouting
  });
</script>

<AlertDialogPrimitive.Root {open} onOpenChange={overlay.handleOpenChange} {...restProps} />

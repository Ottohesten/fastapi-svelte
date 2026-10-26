<script lang="ts">
  import { LoaderCircle } from "@lucide/svelte";
  import BarcodeScanner from "$lib/components/BarcodeScanner.svelte";
  import * as Dialog from "$lib/components/ui/dialog";

  let {
    open = $bindable(false),
    loading = false,
    onDetected,
    title = "Scan a barcode",
    description = "Use the camera or enter the barcode manually.",
    loadingLabel = "Looking up product…"
  }: {
    open?: boolean;
    loading?: boolean;
    onDetected: (barcode: string) => void;
    title?: string;
    description?: string;
    loadingLabel?: string;
  } = $props();
</script>

<Dialog.Root bind:open shallowRouting={false}>
  <Dialog.Content class="barcode-scan-dialog max-h-[90vh] overflow-y-auto sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>{title}</Dialog.Title>
      <Dialog.Description>{description}</Dialog.Description>
    </Dialog.Header>
    {#if loading}
      <div class="text-muted-foreground grid min-h-64 place-items-center">
        <span class="flex items-center gap-2">
          <LoaderCircle class="animate-spin" />
          {loadingLabel}
        </span>
      </div>
    {:else}
      <BarcodeScanner {onDetected} />
    {/if}
  </Dialog.Content>
</Dialog.Root>

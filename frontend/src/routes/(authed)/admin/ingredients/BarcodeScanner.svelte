<script lang="ts">
  import { onMount } from "svelte";
  import { BrowserMultiFormatReader, type IScannerControls } from "@zxing/browser";
  import { Input } from "$lib/components/ui/input";
  import Button from "$lib/components/ui/button/button.svelte";
  import { Camera, Keyboard, LoaderCircle } from "lucide-svelte";

  let { onDetected }: { onDetected: (barcode: string) => void } = $props();

  let video: HTMLVideoElement;
  let controls: IScannerControls | undefined;
  let cameraError = $state("");
  let starting = $state(true);
  let detected = $state(false);
  let manualBarcode = $state("");

  function submitBarcode(barcode: string) {
    const cleaned = barcode.trim();
    if (detected || !/^\d{4,24}$/.test(cleaned)) return;

    detected = true;
    controls?.stop();
    if ("vibrate" in navigator) navigator.vibrate(80);
    onDetected(cleaned);
  }

  onMount(() => {
    const reader = new BrowserMultiFormatReader(undefined, {
      delayBetweenScanAttempts: 150,
      delayBetweenScanSuccess: 1000
    });

    reader
      .decodeFromConstraints(
        { audio: false, video: { facingMode: { ideal: "environment" } } },
        video,
        (result) => {
          if (result) submitBarcode(result.getText());
        }
      )
      .then((scannerControls) => {
        controls = scannerControls;
        starting = false;
      })
      .catch((error: unknown) => {
        starting = false;
        cameraError =
          error instanceof Error && error.name === "NotAllowedError"
            ? "Camera access was denied. Allow camera access or enter the barcode below."
            : "The camera could not be started. You can enter the barcode below instead.";
      });

    return () => controls?.stop();
  });
</script>

<div class="space-y-4">
  <div class="relative aspect-[4/3] overflow-hidden rounded-xl bg-black">
    <video bind:this={video} class="h-full w-full object-cover" muted playsinline></video>
    <div class="pointer-events-none absolute inset-0 grid place-items-center">
      <div
        class="h-28 w-4/5 rounded-lg border-2 border-white shadow-[0_0_0_999px_rgba(0,0,0,0.35)]"
      ></div>
    </div>
    {#if starting}
      <div class="absolute inset-0 grid place-items-center bg-black/60 text-white">
        <div class="flex items-center gap-2 text-sm">
          <LoaderCircle class="size-5 animate-spin" /> Starting camera…
        </div>
      </div>
    {/if}
  </div>

  <div class="bg-muted flex items-start gap-3 rounded-lg p-3 text-sm">
    <Camera class="mt-0.5 size-5 shrink-0" />
    <p>Hold the product barcode inside the frame. Scanning happens automatically.</p>
  </div>

  {#if cameraError}
    <p class="text-sm text-red-600 dark:text-red-400">{cameraError}</p>
  {/if}

  <form
    class="flex gap-2"
    onsubmit={(event) => {
      event.preventDefault();
      submitBarcode(manualBarcode);
    }}
  >
    <div class="relative flex-1">
      <Keyboard class="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
      <Input
        class="pl-9"
        inputmode="numeric"
        autocomplete="off"
        placeholder="Enter barcode manually"
        bind:value={manualBarcode}
        pattern="[0-9]+"
        minlength={4}
        maxlength={24}
        required
      />
    </div>
    <Button type="submit" disabled={detected}>Look up</Button>
  </form>
</div>

<script lang="ts">
  import { onMount } from "svelte";
  import type {
    QuaggaJSConfigObject,
    QuaggaJSResultObject,
    QuaggaJSStatic
  } from "@ericblade/quagga2";
  import {
    Camera,
    Flashlight,
    FlashlightOff,
    ImageUp,
    Keyboard,
    LoaderCircle,
    ScanLine,
    ZoomIn,
    ZoomOut
  } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import {
    clampCameraZoom,
    getCameraZoomConfiguration,
    type CameraZoomCapabilities,
    type CameraZoomConfiguration
  } from "$lib/barcode-scanner";

  type ExtendedCameraCapabilities = MediaTrackCapabilities & {
    focusMode?: string[];
    torch?: boolean;
    zoom?: CameraZoomCapabilities;
  };

  type ExtendedCameraConstraints = MediaTrackConstraintSet & {
    focusMode?: string;
    zoom?: number;
  };

  const PRODUCT_READERS = [
    "ean_reader",
    "ean_8_reader",
    "upc_reader",
    "upc_e_reader",
    "code_128_reader",
    "i2of5_reader",
    "2of5_reader"
  ] as const;

  const LIVE_SCAN_AREA = {
    top: "27%",
    right: "5%",
    bottom: "27%",
    left: "5%"
  };

  let { onDetected }: { onDetected: (barcode: string) => void } = $props();

  let scannerTarget: HTMLDivElement;
  let imageInput: HTMLInputElement;
  let quagga: QuaggaJSStatic | undefined;
  let videoTrack: MediaStreamTrack | undefined;
  let detectedHandler: ((result: QuaggaJSResultObject) => void) | undefined;
  let disposed = false;
  let lastCandidate = "";
  let candidateReads = 0;
  let lastCandidateAt = 0;

  let cameraError = $state("");
  let cameraNotice = $state("");
  let starting = $state(true);
  let detected = $state(false);
  let manualBarcode = $state("");
  let scanningImage = $state(false);
  let zoomConfiguration = $state<CameraZoomConfiguration | null>(null);
  let zoom = $state(1);
  let torchSupported = $state(false);
  let torchOn = $state(false);
  let cameraResolution = $state("");

  function cleanBarcode(barcode: string | null | undefined) {
    return barcode?.trim() ?? "";
  }

  function submitBarcode(barcode: string | null | undefined) {
    const cleaned = cleanBarcode(barcode);
    if (detected || !/^\d{4,24}$/.test(cleaned)) return false;

    detected = true;
    void stopScanning();
    if ("vibrate" in navigator) navigator.vibrate(80);
    onDetected(cleaned);
    return true;
  }

  function confirmLiveDetection(result: QuaggaJSResultObject) {
    const barcode = cleanBarcode(result.codeResult?.code);
    if (!/^\d{4,24}$/.test(barcode)) return;

    const now = Date.now();
    if (barcode !== lastCandidate || now - lastCandidateAt > 1500) {
      lastCandidate = barcode;
      candidateReads = 1;
    } else {
      candidateReads += 1;
    }
    lastCandidateAt = now;

    // A second matching frame removes the majority of live-camera false positives while adding
    // only a fraction of a second at the configured scan frequency.
    if (candidateReads >= 2) submitBarcode(barcode);
  }

  async function stopScanning() {
    if (quagga && detectedHandler) {
      quagga.offDetected(detectedHandler);
      detectedHandler = undefined;
    }

    if (quagga) {
      try {
        await quagga.stop();
      } catch {
        // The camera may already have been released by the browser or its enclosing dialog.
      }
    }

    videoTrack = undefined;
    torchOn = false;
  }

  function updateCameraResolution() {
    const settings = videoTrack?.getSettings();
    cameraResolution =
      settings?.width && settings.height ? `${settings.width} × ${settings.height}` : "";
  }

  async function configureCameraTrack() {
    videoTrack = quagga?.CameraAccess.getActiveTrack() ?? undefined;
    if (!videoTrack) return;

    const capabilities = videoTrack.getCapabilities() as ExtendedCameraCapabilities;
    const settings = videoTrack.getSettings();
    const advanced: ExtendedCameraConstraints = {};

    if (capabilities.focusMode?.includes("continuous")) {
      advanced.focusMode = "continuous";
    }

    zoomConfiguration = getCameraZoomConfiguration(capabilities.zoom, settings.zoom);
    if (zoomConfiguration) {
      zoom = zoomConfiguration.value;
      advanced.zoom = zoom;
    }

    torchSupported = capabilities.torch === true;

    if (Object.keys(advanced).length > 0) {
      try {
        await videoTrack.applyConstraints({ advanced: [advanced] });
      } catch {
        // Experimental camera controls can be advertised but rejected on some mobile browsers.
      }
    }

    updateCameraResolution();
  }

  async function setZoom(requestedZoom: number) {
    if (!videoTrack || !zoomConfiguration) return;

    const nextZoom = clampCameraZoom(requestedZoom, zoomConfiguration);
    try {
      await videoTrack.applyConstraints({
        advanced: [{ zoom: nextZoom } as ExtendedCameraConstraints]
      });
      zoom = videoTrack.getSettings().zoom ?? nextZoom;
      cameraNotice = "";
    } catch {
      cameraNotice = "This camera did not accept the requested zoom level.";
    }
  }

  function changeZoomBy(steps: number) {
    if (zoomConfiguration) {
      setZoom(zoom + zoomConfiguration.step * steps);
    }
  }

  async function toggleTorch() {
    if (!quagga || !torchSupported) return;

    const nextTorchState = !torchOn;
    try {
      if (nextTorchState) await quagga.CameraAccess.enableTorch();
      else await quagga.CameraAccess.disableTorch();
      torchOn = nextTorchState;
      cameraNotice = "";
    } catch {
      cameraNotice = "The light could not be changed on this camera.";
    }
  }

  function scannerConfiguration(): QuaggaJSConfigObject {
    return {
      inputStream: {
        type: "LiveStream",
        target: scannerTarget,
        size: 1280,
        willReadFrequently: true,
        constraints: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30, max: 60 }
        },
        area: LIVE_SCAN_AREA
      },
      locate: true,
      frequency: 10,
      numOfWorkers: 0,
      canvas: { createOverlay: false },
      locator: {
        patchSize: "small",
        halfSample: false,
        willReadFrequently: true
      },
      decoder: {
        readers: [...PRODUCT_READERS],
        multiple: false
      }
    };
  }

  async function startScanning() {
    try {
      const quaggaModule = await import("@ericblade/quagga2");
      if (disposed) return;

      quagga = quaggaModule.default;
      if (!window.isSecureContext && window.location.hostname !== "localhost") {
        starting = false;
        cameraError = "Camera scanning requires HTTPS. Take a photo or enter the barcode below.";
        return;
      }

      await quagga.init(scannerConfiguration());
      if (disposed || detected) {
        await quagga.stop();
        return;
      }

      await configureCameraTrack();
      detectedHandler = confirmLiveDetection;
      quagga.onDetected(detectedHandler);
      quagga.start();
      starting = false;
    } catch (error: unknown) {
      if (disposed) return;
      await stopScanning();
      starting = false;
      cameraError =
        error instanceof Error && error.name === "NotAllowedError"
          ? "Camera access was denied. Allow camera access or enter the barcode below."
          : "The camera could not be started. Take a photo or enter the barcode below instead.";
    }
  }

  async function decodeImage(file: File) {
    if (!quagga || detected) return;

    scanningImage = true;
    cameraNotice = "";
    const imageUrl = URL.createObjectURL(file);

    try {
      const result = await quagga.decodeSingle({
        src: imageUrl,
        locate: true,
        numOfWorkers: 0,
        inputStream: {
          type: "ImageStream",
          size: 1600,
          willReadFrequently: true
        },
        locator: {
          patchSize: "small",
          halfSample: false,
          willReadFrequently: true
        },
        decoder: {
          readers: [...PRODUCT_READERS],
          multiple: false
        }
      });

      if (!submitBarcode(result?.codeResult?.code)) {
        throw new Error("No numeric product barcode was found.");
      }
    } catch {
      cameraNotice =
        "No barcode was found in that photo. Keep the full barcode sharp and include the white space at both ends.";
    } finally {
      URL.revokeObjectURL(imageUrl);
      scanningImage = false;
      imageInput.value = "";
    }
  }

  onMount(() => {
    void startScanning();

    return () => {
      disposed = true;
      void stopScanning();
    };
  });
</script>

<div class="space-y-4">
  <div class="relative aspect-[4/3] overflow-hidden rounded-xl bg-black">
    <div
      bind:this={scannerTarget}
      class="absolute inset-0 overflow-hidden [&_canvas]:absolute [&_canvas]:inset-0 [&_canvas]:size-full [&_video]:size-full [&_video]:object-contain"
    ></div>
    <div class="pointer-events-none absolute inset-0 grid place-items-center">
      <div
        class="relative h-[46%] w-[90%] rounded-lg border-2 border-white shadow-[0_0_0_999px_rgba(0,0,0,0.38)]"
      >
        <div
          class="absolute top-1/2 right-3 left-3 h-px -translate-y-1/2 bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.9)]"
        ></div>
      </div>
    </div>
    {#if starting}
      <div class="absolute inset-0 grid place-items-center bg-black/60 text-white">
        <div class="flex items-center gap-2 text-sm">
          <LoaderCircle class="size-5 animate-spin" /> Starting camera…
        </div>
      </div>
    {:else if !cameraError && !detected}
      <div
        class="absolute top-3 left-3 flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1 text-xs text-white"
      >
        <ScanLine class="size-3.5" /> Scanning{cameraResolution ? ` · ${cameraResolution}` : ""}
      </div>
    {/if}
  </div>

  {#if !cameraError && (zoomConfiguration || torchSupported)}
    <div class="bg-muted/60 space-y-3 rounded-lg border p-3">
      {#if zoomConfiguration}
        <div class="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Zoom out"
            onclick={() => changeZoomBy(-1)}
          >
            <ZoomOut class="size-4" />
          </Button>
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <label for="barcode-camera-zoom" class="font-medium">Camera zoom</label>
              <span class="text-muted-foreground">{zoom.toFixed(1)}×</span>
            </div>
            <input
              id="barcode-camera-zoom"
              class="accent-primary h-5 w-full cursor-pointer"
              type="range"
              min={zoomConfiguration.min}
              max={zoomConfiguration.max}
              step={zoomConfiguration.step}
              value={zoom}
              oninput={(event) => setZoom(Number(event.currentTarget.value))}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Zoom in"
            onclick={() => changeZoomBy(1)}
          >
            <ZoomIn class="size-4" />
          </Button>
        </div>
      {/if}

      {#if torchSupported}
        <Button type="button" variant="outline" class="w-full" onclick={toggleTorch}>
          {#if torchOn}
            <FlashlightOff class="size-4" /> Turn light off
          {:else}
            <Flashlight class="size-4" /> Turn light on
          {/if}
        </Button>
      {/if}
    </div>
  {/if}

  <div class="bg-muted flex items-start gap-3 rounded-lg p-3 text-sm">
    <Camera class="mt-0.5 size-5 shrink-0" />
    <p>
      Fill most of the frame with the barcode, but keep every line and the white space at both ends
      visible. Move closer or farther away until the lines are sharp.
    </p>
  </div>

  {#if cameraError}
    <p class="text-destructive text-sm">{cameraError}</p>
  {/if}
  {#if cameraNotice}
    <p class="text-muted-foreground text-sm">{cameraNotice}</p>
  {/if}

  <input
    bind:this={imageInput}
    class="sr-only"
    type="file"
    accept="image/*"
    capture="environment"
    aria-label="Choose a barcode photo"
    onchange={(event) => {
      const file = event.currentTarget.files?.[0];
      if (file) decodeImage(file);
    }}
  />
  <Button
    type="button"
    variant="outline"
    class="w-full"
    disabled={detected || scanningImage}
    onclick={() => imageInput.click()}
  >
    {#if scanningImage}
      <LoaderCircle class="size-4 animate-spin" /> Reading photo…
    {:else}
      <ImageUp class="size-4" /> Take or choose photo
    {/if}
  </Button>

  <form
    class="flex gap-2"
    onsubmit={(event) => {
      event.preventDefault();
      submitBarcode(manualBarcode);
    }}
  >
    <div class="relative min-w-0 flex-1">
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

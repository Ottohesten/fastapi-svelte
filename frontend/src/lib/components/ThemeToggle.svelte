<script lang="ts">
  import { onMount } from "svelte";
  import Check from "@lucide/svelte/icons/check";
  import Monitor from "@lucide/svelte/icons/monitor";
  import Moon from "@lucide/svelte/icons/moon";
  import Sun from "@lucide/svelte/icons/sun";
  import { Button } from "$lib/components/ui/button";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";

  type Theme = "light" | "dark" | "system";

  const options: { value: Theme; label: string; icon: typeof Sun }[] = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "system", label: "System", icon: Monitor }
  ];

  let theme = $state<Theme>("system");
  let systemMedia: MediaQueryList;

  function isTheme(value: string | null): value is Theme {
    return value === "light" || value === "dark" || value === "system";
  }

  function applyTheme(value: Theme) {
    const dark = value === "dark" || (value === "system" && systemMedia.matches);
    document.documentElement.classList.toggle("dark", dark);
    document.documentElement.style.colorScheme = dark ? "dark" : "light";
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", dark ? "#0b1220" : "#ffffff");
  }

  function setTheme(value: Theme) {
    theme = value;
    localStorage.setItem("theme", value);
    applyTheme(value);
    window.dispatchEvent(new CustomEvent<Theme>("app-theme-change", { detail: value }));
  }

  onMount(() => {
    systemMedia = window.matchMedia("(prefers-color-scheme: dark)");
    const saved = localStorage.getItem("theme");
    theme = isTheme(saved) ? saved : "system";
    applyTheme(theme);

    const handleSystemChange = () => {
      if (theme === "system") applyTheme(theme);
    };
    const handleThemeChange = (event: Event) => {
      const value = (event as CustomEvent<Theme>).detail;
      if (!isTheme(value)) return;
      theme = value;
      applyTheme(value);
    };
    const handleStorage = (event: StorageEvent) => {
      if (event.key !== "theme" || !isTheme(event.newValue)) return;
      theme = event.newValue;
      applyTheme(theme);
    };

    systemMedia.addEventListener("change", handleSystemChange);
    window.addEventListener("app-theme-change", handleThemeChange);
    window.addEventListener("storage", handleStorage);

    return () => {
      systemMedia.removeEventListener("change", handleSystemChange);
      window.removeEventListener("app-theme-change", handleThemeChange);
      window.removeEventListener("storage", handleStorage);
    };
  });
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger>
    {#snippet child({ props })}
      <Button
        {...props}
        variant="ghost"
        size="icon"
        class="relative"
        aria-label="Change color theme"
        title="Change color theme"
      >
        {#if theme === "light"}
          <Sun />
        {:else if theme === "dark"}
          <Moon />
        {:else}
          <Monitor />
        {/if}
      </Button>
    {/snippet}
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="end" class="w-40">
    <DropdownMenu.Label>Appearance</DropdownMenu.Label>
    <DropdownMenu.Separator />
    {#each options as option (option.value)}
      <DropdownMenu.Item onclick={() => setTheme(option.value)}>
        <option.icon />
        <span>{option.label}</span>
        {#if theme === option.value}
          <Check class="ml-auto" />
        {/if}
      </DropdownMenu.Item>
    {/each}
  </DropdownMenu.Content>
</DropdownMenu.Root>

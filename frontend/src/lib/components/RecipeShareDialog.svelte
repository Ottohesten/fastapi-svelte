<script lang="ts">
  import { Copy, Download, Link, Share2 } from "@lucide/svelte";
  import type { RecipePublic } from "#lib/client/index.js";
  import { Button, buttonVariants } from "#lib/components/ui/button/index.js";
  import * as Dialog from "#lib/components/ui/dialog/index.js";
  import { Input } from "#lib/components/ui/input/index.js";
  import { ingredientListText } from "#lib/recipes/sharing.js";

  let { recipe, recipeUrl }: { recipe: RecipePublic; recipeUrl: string } = $props();
  let open = $state(false);
  let copyStatus = $state("");
  const listText = $derived(
    ingredientListText(recipe.title, recipe.servings, recipe.total_ingredients)
  );

  async function copyText(text: string, success: string) {
    try {
      await navigator.clipboard.writeText(text);
      copyStatus = success;
    } catch {
      copyStatus = "Copy unavailable. Select the list or link and copy it manually.";
    }
  }

  function downloadList() {
    const blob = new Blob([listText + "\n"], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const filename =
      recipe.title
        .toLowerCase()
        .replace(/[^\p{L}\p{N}]+/gu, "-")
        .replace(/^-|-$/g, "") || "recipe";
    anchor.href = url;
    anchor.download = `${filename}-ingredients-${recipe.servings}-servings.txt`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Trigger
    class={buttonVariants({ variant: "outline", size: "sm" })}
    onclick={() => (copyStatus = "")}
  >
    <Share2 class="size-4" /> Share ingredients
  </Dialog.Trigger>
  <Dialog.Content class="sm:max-w-xl">
    <Dialog.Header>
      <Dialog.Title>Share ingredients</Dialog.Title>
      <Dialog.Description>
        Copy or download the full ingredient list for {recipe.servings}
        {recipe.servings === 1 ? "serving" : "servings"}, including linked sub-recipes.
      </Dialog.Description>
    </Dialog.Header>

    <label for="recipe-share-link" class="text-sm font-medium">Recipe link</label>
    <Input
      id="recipe-share-link"
      readonly
      value={recipeUrl}
      onfocus={(event) => event.currentTarget.select()}
    />
    <Button variant="outline" onclick={() => copyText(recipeUrl, "Recipe link copied.")}>
      <Link /> Copy recipe link
    </Button>

    <label for="recipe-ingredient-list" class="text-sm font-medium">Ingredient list</label>
    <textarea
      id="recipe-ingredient-list"
      readonly
      value={listText}
      rows={10}
      class="border-input bg-background focus-visible:ring-ring max-h-[40dvh] w-full resize-y rounded-md border p-3 text-sm focus-visible:ring-2 focus-visible:outline-none"
      onfocus={(event) => event.currentTarget.select()}></textarea>
    <p role="status" class="text-muted-foreground min-h-5 text-sm">{copyStatus}</p>

    <Dialog.Footer class="gap-2">
      <Button variant="outline" onclick={downloadList}><Download /> Download .txt</Button>
      <Button onclick={() => copyText(listText, "Ingredient list copied.")}>
        <Copy /> Copy list
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

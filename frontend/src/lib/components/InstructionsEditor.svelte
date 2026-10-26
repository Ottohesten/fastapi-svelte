<script lang="ts">
  import "./styles.scss";

  import { Color, TextStyle } from "@tiptap/extension-text-style";
  import StarterKit from "@tiptap/starter-kit";
  import { Editor } from "@tiptap/core";
  import { NodeSelection } from "@tiptap/pm/state";
  import { onMount, onDestroy } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import * as Dialog from "$lib/components/ui/dialog";
  import { IngredientAmountNode } from "$lib/recipes/ingredient-amount-node";
  import { SubRecipeInstructionNode } from "$lib/recipes/sub-recipe-instruction-node";
  import {
    linkSubRecipeInstructions,
    type InstructionRecipe
  } from "$lib/recipes/sub-recipe-instructions";
  import {
    decodeAmountReference,
    encodeAmountReference,
    ingredientAmountScope,
    parseIngredientPortion,
    resolveIngredientAmount,
    type AmountIngredient,
    type AmountRecipe,
    type IngredientAmountReference
  } from "$lib/recipes/ingredient-amounts";

  let {
    value = $bindable(""),
    amountRecipe = { id: "", total_ingredients: [] },
    recipes = []
  }: {
    value?: string;
    amountRecipe?: AmountRecipe;
    recipes?: (AmountRecipe & InstructionRecipe)[];
  } = $props();

  let element: HTMLDivElement;
  let editor = $state.raw<Editor | null>(null);
  let editorReady = $state(false);
  let editorState = $state(0); // Counter to force reactivity

  const EMPTY_PARAGRAPH = "<p></p>";
  let lastInternalValue = "";
  let isApplyingExternalContent = false;
  let lastAppliedExternalValue = "";
  let amountPickerOpen = $state(false);
  let amountIngredientKey = $state("");
  let amountPortion = $state("100%");
  let amountPath = $state<string[]>([]);
  let amountRange = { from: 0, to: 0 };

  const pickerIngredients = $derived(
    ingredientAmountScope(amountPath, amountRecipe, recipes)?.recipe.total_ingredients ?? []
  );
  const selectedAmountIngredient = $derived(
    pickerIngredients.find((ingredient) => ingredientKey(ingredient) === amountIngredientKey)
  );
  const amountReference = $derived.by<IngredientAmountReference | null>(() => {
    if (!selectedAmountIngredient || parseIngredientPortion(amountPortion) === null) return null;
    return {
      ingredientId: selectedAmountIngredient.ingredient_id,
      title: selectedAmountIngredient.title,
      unit: selectedAmountIngredient.unit,
      portion: amountPortion.trim(),
      path: amountPath
    };
  });
  const amountPreview = $derived(
    amountReference ? resolveIngredientAmount(amountReference, amountRecipe, recipes) : null
  );

  function ingredientKey(ingredient: AmountIngredient): string {
    return JSON.stringify([ingredient.ingredient_id, ingredient.unit]);
  }

  function openAmountPicker(reference: IngredientAmountReference, position: number) {
    if (!editor) return;
    amountRange = { from: position, to: position + 1 };
    amountPath = reference.path;
    amountIngredientKey = JSON.stringify([reference.ingredientId, reference.unit]);
    amountPortion = reference.portion;
    amountPickerOpen = true;
  }

  function insertIngredientAmount() {
    if (!editor || !amountReference) return;
    editor.commands.insertContentAt(amountRange, {
      type: "ingredientAmount",
      attrs: { reference: encodeAmountReference(amountReference) }
    });
    amountPickerOpen = false;
  }

  function normalizeHtml(html: string | null | undefined) {
    if (html === undefined || html === null || html === EMPTY_PARAGRAPH) {
      return "";
    }

    return linkSubRecipeInstructions(html, amountRecipe.sub_recipe_links, recipes);
  }

  function normalizeForCompare(html: string | null | undefined) {
    return normalizeHtml(html)
      .replaceAll("&nbsp;", " ")
      .replaceAll("\u00A0", " ")
      .replace(/>\s+</g, "><")
      .trim();
  }

  $effect(() => {
    if (!editorReady || !editor || value === undefined) {
      return;
    }

    if (isApplyingExternalContent) {
      return;
    }

    const normalizedValue = normalizeForCompare(value);
    const normalizedCurrentHtml = normalizeForCompare(editor.getHTML());
    const normalizedLastInternalValue = normalizeForCompare(lastInternalValue);
    const normalizedLastAppliedExternalValue = normalizeForCompare(lastAppliedExternalValue);

    // Ignore updates that originated from this editor instance.
    if (normalizedValue === normalizedLastInternalValue) {
      return;
    }

    // Ignore repeated attempts to apply the same external HTML.
    if (normalizedValue === normalizedLastAppliedExternalValue) {
      return;
    }

    // Apply only truly external changes (restore/reset/etc).
    if (normalizedValue !== normalizedCurrentHtml) {
      isApplyingExternalContent = true;
      lastAppliedExternalValue = normalizeHtml(value);
      lastInternalValue = normalizeHtml(value);
      editor.commands.setContent(normalizeHtml(value), { emitUpdate: false });
      const canonical = editor.getHTML();
      if (value !== canonical) {
        lastInternalValue = canonical;
        value = canonical;
      }
      queueMicrotask(() => {
        isApplyingExternalContent = false;
      });
    }
  });

  onDestroy(() => {
    if (editor) {
      editor.destroy();
      editor = null;
      editorReady = false;
    }
  });

  onMount(() => {
    editor = new Editor({
      element: element,
      extensions: [
        Color.configure({ types: [TextStyle.name, "listItem"] }),
        TextStyle,
        StarterKit,
        IngredientAmountNode.configure({ getIngredients: () => amountRecipe.total_ingredients }),
        SubRecipeInstructionNode
      ],
      content: normalizeHtml(value),
      editorProps: {
        handleClickOn: (_view, _pos, node, nodePos, _event, direct) => {
          if (!direct || node.type.name !== "ingredientAmount") return false;
          const reference = decodeAmountReference(node.attrs.reference);
          if (!reference) return false;
          openAmountPicker(reference, nodePos);
          return true;
        },
        handleKeyDown: (view, event) => {
          const selection = view.state.selection;
          if (
            event.key !== "Enter" ||
            !(selection instanceof NodeSelection) ||
            selection.node.type.name !== "ingredientAmount"
          ) {
            return false;
          }
          const reference = decodeAmountReference(selection.node.attrs.reference);
          if (!reference) return false;
          openAmountPicker(reference, selection.from);
          return true;
        },
        attributes: {
          class:
            "prose dark:prose-invert focus:outline-none min-h-[200px] p-4 border border-gray-300 rounded-lg bg-white text-gray-900 w-full max-w-none dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100"
        }
      },
      onTransaction: () => {
        // Force re-render by incrementing state counter
        editorState++;
      },
      onUpdate: ({ editor }) => {
        // Update the bound value with HTML content
        if (value !== undefined) {
          const html = editor.getHTML();
          lastInternalValue = html;
          if (value !== html) {
            value = html;
          }
        }
      }
    });
    editorReady = true;
    // Persist stable recipe links when an existing copied section is first opened.
    if (normalizeHtml(value) !== value) {
      lastInternalValue = editor.getHTML();
      value = lastInternalValue;
    }
  });

  // Reactive function to check if editor is active (depends on editorState)
  function isActive(name: string, attributes?: Record<string, unknown>) {
    editorState; // Access the state to create reactivity
    return editor?.isActive(name, attributes) || false;
  }

  function canPerformAction(action: string) {
    editorState; // Access the state to create reactivity
    if (!editor) return false;

    switch (action) {
      case "toggleBold":
        return editor.can().chain().toggleBold().run();
      case "toggleItalic":
        return editor.can().chain().toggleItalic().run();
      case "undo":
        return editor.can().chain().undo().run();
      case "redo":
        return editor.can().chain().redo().run();
      default:
        return false;
    }
  }
</script>

{#if editorReady && editor}
  <div class="control-group mb-2">
    <div class="button-group flex flex-wrap gap-1">
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleBold().run()}
        disabled={!canPerformAction("toggleBold")}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('bold')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        <strong>B</strong>
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleItalic().run()}
        disabled={!canPerformAction("toggleItalic")}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('italic')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        <em>I</em>
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('heading', { level: 2 })
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        H2
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('heading', { level: 3 })
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        H3
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleBulletList().run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('bulletList')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        • List
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().toggleOrderedList().run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('orderedList')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        1. List
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().undo().run()}
        disabled={!canPerformAction("undo")}
        class="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
      >
        ↶
      </button>
      <button
        type="button"
        onclick={() => editor?.chain().focus().redo().run()}
        disabled={!canPerformAction("redo")}
        class="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
      >
        ↷
      </button>
    </div>
  </div>
{/if}
<div bind:this={element} class="w-full"></div>

<Dialog.Root bind:open={amountPickerOpen} shallowRouting={false}>
  <Dialog.Content
    class="sm:max-w-md"
    onCloseAutoFocus={(event) => {
      event.preventDefault();
      editor?.commands.focus();
    }}
  >
    <Dialog.Header>
      <Dialog.Title>Ingredient amount</Dialog.Title>
      <Dialog.Description>
        Choose a portion of an ingredient. Its amount will update with the recipe's servings.
      </Dialog.Description>
    </Dialog.Header>
    <Label for="instruction-amount-ingredient">Ingredient</Label>
    <select
      id="instruction-amount-ingredient"
      bind:value={amountIngredientKey}
      class="border-input bg-background h-10 w-full rounded-md border px-3 text-sm"
    >
      {#each pickerIngredients as ingredient (ingredientKey(ingredient))}
        <option value={ingredientKey(ingredient)}>{ingredient.title} ({ingredient.unit})</option>
      {/each}
    </select>
    {#if amountPath.length > 0}
      <p class="text-muted-foreground text-sm">
        This reference uses the linked sub-recipe's quantities.
      </p>
    {/if}
    <Label for="instruction-amount-portion">Portion</Label>
    <Input id="instruction-amount-portion" bind:value={amountPortion} placeholder="25% or 1/2" />
    {#if parseIngredientPortion(amountPortion) === null}
      <p class="text-destructive text-sm" role="alert">
        Enter a percentage up to 100% or a fraction up to 1, such as 25% or 1/2.
      </p>
    {/if}
    <p class="text-muted-foreground text-sm" role="status">
      {amountPreview
        ? `At the recipe's original servings: ${amountPreview}`
        : "Ingredient unavailable. Add or select an ingredient first."}
    </p>
    <Dialog.Footer>
      <Button onclick={insertIngredientAmount} disabled={!amountReference}>Insert amount</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>

<style>
  :global(.tiptap .ingredient-amount-reference) {
    border-radius: 0.25rem;
    background: var(--color-accent);
    color: var(--color-accent-foreground);
    padding: 0.125rem 0.25rem;
    cursor: pointer;
    box-decoration-break: clone;
  }
  :global(.tiptap .ingredient-amount-reference.ProseMirror-selectednode) {
    outline: 2px solid var(--color-ring);
  }
</style>

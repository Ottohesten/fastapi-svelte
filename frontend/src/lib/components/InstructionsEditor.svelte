<script lang="ts">
  // @ts-nocheck
  import "./styles.scss";

  import { Color } from "@tiptap/extension-text-style";
  import { BulletList, ListItem } from "@tiptap/extension-list";
  import { TextStyle } from "@tiptap/extension-text-style";
  import StarterKit from "@tiptap/starter-kit";
  import { Editor } from "@tiptap/core";
  import { onMount, onDestroy } from "svelte";

  let { value = $bindable("") } = $props();

  let element;
  let editor = $state.raw<Editor | null>(null);
  let editorReady = $state(false);
  let editorState = $state(0); // Counter to force reactivity

  const EMPTY_PARAGRAPH = "<p></p>";
  let lastInternalValue = "";
  let isApplyingExternalContent = false;
  let lastAppliedExternalValue = "";

  function normalizeHtml(html: string | null | undefined) {
    if (html === undefined || html === null || html === EMPTY_PARAGRAPH) {
      return "";
    }

    return html;
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
        Color.configure({ types: [TextStyle.name, ListItem.name] }),
        TextStyle.configure({ types: [ListItem.name] }),
        StarterKit
      ],
      content: normalizeHtml(value),
      editorProps: {
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
  });

  // Reactive function to check if editor is active (depends on editorState)
  function isActive(name, attributes) {
    editorState; // Access the state to create reactivity
    return editor?.isActive(name, attributes) || false;
  }

  function canPerformAction(action) {
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
        onclick={() => editor.chain().focus().toggleBold().run()}
        disabled={!canPerformAction("toggleBold")}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('bold')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        <strong>B</strong>
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().toggleItalic().run()}
        disabled={!canPerformAction("toggleItalic")}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('italic')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        <em>I</em>
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('heading', { level: 2 })
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        H2
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('heading', { level: 3 })
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        H3
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().toggleBulletList().run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('bulletList')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        • List
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().toggleOrderedList().run()}
        class="rounded border border-gray-300 px-2 py-1 text-xs {isActive('orderedList')
          ? 'bg-gray-800 text-white'
          : 'bg-white text-gray-700 dark:bg-gray-900/40 dark:text-gray-200'} hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-gray-800"
      >
        1. List
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().undo().run()}
        disabled={!canPerformAction("undo")}
        class="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
      >
        ↶
      </button>
      <button
        type="button"
        onclick={() => editor.chain().focus().redo().run()}
        disabled={!canPerformAction("redo")}
        class="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-200 dark:hover:bg-gray-800"
      >
        ↷
      </button>
    </div>
  </div>
{/if}
<div bind:this={element} class="w-full"></div>

<script lang="ts">
	// @ts-nocheck
	import './styles.scss';

	import { Color } from '@tiptap/extension-color';
	import ListItem from '@tiptap/extension-list-item';
	import TextStyle from '@tiptap/extension-text-style';
	import StarterKit from '@tiptap/starter-kit';
	import { Editor } from '@tiptap/core';
	import { onMount, onDestroy } from 'svelte';

	let { value = $bindable(''), placeholder = 'Enter instructions...' } = $props();

	let element;
	let editor = $state();

	onMount(() => {
		editor = new Editor({
			element: element,
			extensions: [
				Color.configure({ types: [TextStyle.name, ListItem.name] }),
				TextStyle.configure({ types: [ListItem.name] }),
				StarterKit
			],
			content: value || '<p></p>',
			editorProps: {
				attributes: {
					class:
						'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[200px] p-4 border rounded-md bg-gray-50'
				}
			},
			onTransaction: () => {
				// force re-render so `editor.isActive` works as expected
				editor = editor;
			},
			onUpdate: ({ editor }) => {
				// Update the bound value with HTML content
				value = editor.getHTML();
			}
		});

		// If there's an initial value, set it
		if (value && value !== '<p></p>') {
			editor.commands.setContent(value);
		}
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});

	// Update editor content when value changes externally
	$effect(() => {
		if (editor && value !== editor.getHTML()) {
			editor.commands.setContent(value || '<p></p>');
		}
	});
</script>

<div class="instructions-editor">
	{#if editor}
		<div class="control-group mb-2">
			<div class="button-group flex flex-wrap gap-1">
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleBold().run()}
					disabled={!editor.can().chain().focus().toggleBold().run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('bold')
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100 disabled:opacity-50"
				>
					<strong>B</strong>
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleItalic().run()}
					disabled={!editor.can().chain().focus().toggleItalic().run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('italic')
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100 disabled:opacity-50"
				>
					<em>I</em>
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleBulletList().run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('bulletList')
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100"
				>
					• List
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleOrderedList().run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('orderedList')
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100"
				>
					1. List
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('heading', { level: 2 })
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100"
				>
					H2
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
					class="rounded border px-2 py-1 text-xs {editor.isActive('heading', { level: 3 })
						? 'bg-gray-800 text-white'
						: 'bg-white text-gray-700'} hover:bg-gray-100"
				>
					H3
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().undo().run()}
					disabled={!editor.can().chain().focus().undo().run()}
					class="rounded border bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50"
				>
					↶
				</button>
				<button
					type="button"
					onclick={() => editor.chain().focus().redo().run()}
					disabled={!editor.can().chain().focus().redo().run()}
					class="rounded border bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50"
				>
					↷
				</button>
			</div>
		</div>
	{/if}
	<div bind:this={element} class="tiptap-container"></div>
</div>

<style>
	.instructions-editor {
		width: 100%;
	}

	.tiptap-container :global(.tiptap) {
		outline: none;
	}

	.tiptap-container :global(.tiptap:empty::before) {
		content: attr(data-placeholder);
		float: left;
		color: #adb5bd;
		pointer-events: none;
		height: 0;
	}
</style>

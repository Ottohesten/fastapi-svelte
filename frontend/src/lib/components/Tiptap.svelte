<script>
	// @ts-nocheck
	import './styles.scss';

	import { Color } from '@tiptap/extension-text-style';
	import { BulletList, ListItem } from '@tiptap/extension-list';
	import { TextStyle } from '@tiptap/extension-text-style';
	import StarterKit from '@tiptap/starter-kit';
	import { Editor } from '@tiptap/core';
	import { onMount } from 'svelte';

	let element;
	let editor;
	let editor_html;

	onMount(() => {
		editor = new Editor({
			element: element,
			extensions: [
				Color.configure({ types: [TextStyle.name, ListItem.name] }),
				TextStyle.configure({ types: [ListItem.name] }),
				BulletList,
				ListItem,
				StarterKit
			],
			editorProps: {
				attributes: {
					class:
						'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[200px] p-4 border rounded-md bg-gray-50'
				}
			},
			content: `
            <h2>
              Hi there,
            </h2>
            <p>
              this is a <em>basic</em> example of <strong>Tiptap</strong>. Sure, there are all kind of basic text styles you'd probably expect from a text editor. But wait until you see the lists:
            </p>
            <ul>
              <li>
                That's a bullet list with one …
              </li>
              <li>
                … or two list items.
              </li>
            </ul>
            <p>
              Isn't that great? And all of that is editable. But wait, there's more. Let's try a code block:
            </p>
            <pre><code class="language-css">body {
  display: none;
}</code></pre>
            <p>
              I know, I know, this is impressive. It's only the tip of the iceberg though. Give it a try and click a little bit around. Don't forget to check the other examples too.
            </p>
            <blockquote>
              Wow, that's amazing. Good work, boy! 👏
              <br />
              — Mom
            </blockquote>
          `,
			onTransaction: () => {
				// force re-render so `editor.isActive` works as expected
				editor = editor;
			},
			onUpdate: ({ editor }) => {
				// Update the bound value with HTML content
				editor_html = editor.getHTML();
			}
		});
	});
</script>

{#if editor}
	<div class="control-group">
		<div class="button-group">
			<button
				onclick={() => console.log && editor.chain().focus().toggleBold().run()}
				disabled={!editor.can().chain().focus().toggleBold().run()}
				class={editor.isActive('bold') ? 'is-active' : ''}
			>
				Bold
			</button>
			<button
				onclick={() => editor.chain().focus().toggleItalic().run()}
				disabled={!editor.can().chain().focus().toggleItalic().run()}
				class={editor.isActive('italic') ? 'is-active' : ''}
			>
				Italic
			</button>
			<button
				onclick={() => editor.chain().focus().toggleStrike().run()}
				disabled={!editor.can().chain().focus().toggleStrike().run()}
				class={editor.isActive('strike') ? 'is-active' : ''}
			>
				Strike
			</button>
			<button
				onclick={() => editor.chain().focus().toggleCode().run()}
				disabled={!editor.can().chain().focus().toggleCode().run()}
				class={editor.isActive('code') ? 'is-active' : ''}
			>
				Code
			</button>
			<button onclick={() => editor.chain().focus().unsetAllMarks().run()}>Clear marks</button>
			<button onclick={() => editor.chain().focus().clearNodes().run()}>Clear nodes</button>
			<button
				onclick={() => editor.chain().focus().setParagraph().run()}
				class={editor.isActive('paragraph') ? 'is-active' : ''}
			>
				Paragraph
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
				class={editor.isActive('heading', { level: 1 }) ? 'is-active' : ''}
			>
				H1
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
				class={editor.isActive('heading', { level: 2 }) ? 'is-active' : ''}
			>
				H2
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
				class={editor.isActive('heading', { level: 3 }) ? 'is-active' : ''}
			>
				H3
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 4 }).run()}
				class={editor.isActive('heading', { level: 4 }) ? 'is-active' : ''}
			>
				H4
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 5 }).run()}
				class={editor.isActive('heading', { level: 5 }) ? 'is-active' : ''}
			>
				H5
			</button>
			<button
				onclick={() => editor.chain().focus().toggleHeading({ level: 6 }).run()}
				class={editor.isActive('heading', { level: 6 }) ? 'is-active' : ''}
			>
				H6
			</button>
			<button
				onclick={() => editor.chain().focus().toggleBulletList().run()}
				class={editor.isActive('bulletList') ? 'is-active' : ''}
			>
				Bullet list
			</button>
			<button
				onclick={() => editor.chain().focus().toggleOrderedList().run()}
				class={editor.isActive('orderedList') ? 'is-active' : ''}
			>
				Ordered list
			</button>
			<button
				onclick={() => editor.chain().focus().toggleCodeBlock().run()}
				class={editor.isActive('codeBlock') ? 'is-active' : ''}
			>
				Code block
			</button>
			<button
				onclick={() => editor.chain().focus().toggleBlockquote().run()}
				class={editor.isActive('blockquote') ? 'is-active' : ''}
			>
				Blockquote
			</button>
			<button onclick={() => editor.chain().focus().setHorizontalRule().run()}>
				Horizontal rule
			</button>
			<button onclick={() => editor.chain().focus().setHardBreak().run()}>Hard break</button>
			<button
				onclick={() => editor.chain().focus().undo().run()}
				disabled={!editor.can().chain().focus().undo().run()}
			>
				Undo
			</button>
			<button
				onclick={() => editor.chain().focus().redo().run()}
				disabled={!editor.can().chain().focus().redo().run()}
			>
				Redo
			</button>
			<button
				onclick={() => editor.chain().focus().setColor('#958DF1').run()}
				class={editor.isActive('textStyle', { color: '#958DF1' }) ? 'is-active' : ''}
			>
				Purple
			</button>
		</div>
	</div>
{/if}
<div bind:this={element} />

<script lang="ts">
	import type { components } from '$lib/api/v1';
	type Props = {
		session: components['schemas']['GameSessionPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};
	let { session, authenticatedUser }: Props = $props();
</script>

<div
	class="my-4 rounded-md border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900/50"
>
	<a href="/game/{session.id}">
		<p>Title: {session.title}</p>
		<p>Owner: {session.owner.email}</p>
	</a>
</div>

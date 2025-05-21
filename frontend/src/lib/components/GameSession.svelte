<script lang="ts">
	import type { components } from '$lib/api/v1';
	type Props = {
		session: components['schemas']['GameSessionPublic'];
		authenticatedUser?: components['schemas']['UserPublic'];
	};
	let { session, authenticatedUser }: Props = $props();
</script>

<div class="my-4 rounded-md bg-gray-100 p-4 dark:bg-gray-800">
	<a href="/game/{session.id}">
		<p>Title: {session.title}</p>
		<p>Owner: {session.owner.email}</p>
	</a>
</div>

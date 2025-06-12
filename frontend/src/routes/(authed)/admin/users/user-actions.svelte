<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';

	import type { components } from '$lib/api/v1';

	let { user }: { user: components['schemas']['UserPublic'] } = $props();
</script>

<div class="flex items-center justify-end space-x-0">
	<Button variant="ghost" title="Edit user" size="sm" class="p-2">
		<Pencil class="" />
	</Button>

	<form action="?/deleteUser" method="POST" use:enhance>
		<input type="hidden" name="user_id" value={user.id} />
		<Button
			variant="ghost"
			title="Delete user"
			size="sm"
			class="p-2 text-red-600 hover:bg-red-100 hover:text-red-700"
			type="submit"
			onclick={(e) => {
				const confirmed = confirm(
					`Are you sure you want to delete user "${user.email}"? This action cannot be undone.`
				);
				if (!confirmed) {
					e.preventDefault();
				}
			}}
		>
			<Trash2 class="" />
		</Button>
	</form>
</div>

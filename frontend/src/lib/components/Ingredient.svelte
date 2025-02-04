<script lang="ts">
	// let stuff = $props();
	let { user, ingredient } = $props();
	import { enhance } from '$app/forms';
</script>

<div class="my-4 rounded-md bg-gray-100 p-4">
	<a href="/ingredients/{ingredient.id}">
		<div class="test">
			<h3 class="font-bold">{ingredient.title}</h3>
			<div class="mt-4 flex flex-col justify-between lg:flex-row"></div>
		</div>
	</a>
	<!-- {#if (user && user.id === ingredient.owner.id) || (user && user.is_superuser)} -->
	{#if user && user.is_superuser}
		<div class="mt-2 flex space-x-4">
			<a
				href="/ingredients/{ingredient.id}/update"
				class="rounded-md bg-gray-600 px-4 py-2 font-medium text-gray-300 hover:bg-gray-900 hover:text-white"
				>Edit</a
			>
			<!-- delete -->
			<form action="/ingredients?/delete" method="POST" use:enhance>
				<input type="hidden" name="ingredient_id" value={ingredient.id} />
				<button
					class="rounded-md bg-red-600 px-4 py-2 font-medium text-gray-300 hover:bg-red-900 hover:text-white"
					type="submit"
				>
					Delete
				</button>
			</form>
		</div>
	{/if}
</div>

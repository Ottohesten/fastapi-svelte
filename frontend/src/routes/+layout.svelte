<script lang="ts">
	import '../app.css';
	let { children, data } = $props();

	// when a new a tag is clicked we need to add some new classes to it and remove some from the last one that was the clicked one

	let activeButton = $state('home');

	function setActiveButton(button: string) {
		activeButton = button;
	}

	// $inspect(activeButton);

	let routes = ['home', 'about', 'blog', 'temp'];
</script>

<nav class="bg-gray-800">
	<div class="px-2 sm:px-6 lg:px-12">
		<div class="relative flex h-16 items-center justify-between">
			<div class="flex items-center space-x-0 sm:space-x-4">
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'home'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					aria-current={activeButton === 'home'}
					href="/"
					onclick={() => (activeButton = 'home')}>Home</a
				>
				{#if data.authenticatedUser}
					<a
						class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'tiptap'
							? 'bg-gray-900 text-white'
							: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
						href="/tiptap"
						aria-current={activeButton === 'tiptap'}
						onclick={() => (activeButton = 'tiptap')}>Tiptap</a
					>
					<a
						class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'hero'
							? 'bg-gray-900 text-white'
							: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
						href="/hero"
						aria-current={activeButton === 'hero'}
						onclick={() => (activeButton = 'hero')}>Hero</a
					>
					<a
						class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'recipes'
							? 'bg-gray-900 text-white'
							: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
						href="/recipes"
						aria-current={activeButton === 'recipes'}
						onclick={() => (activeButton = 'recipes')}>Recipes</a
					>
					<a
						class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'ingredients'
							? 'bg-gray-900 text-white'
							: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
						href="/ingredients"
						aria-current={activeButton === 'ingredients'}
						onclick={() => (activeButton = 'ingredients')}>Ingredients</a
					>
				{/if}
			</div>

			<!-- make some icons that are all the way to the right -->
			<div class="flex space-x-2">
				<a
					class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white"
					href="/admin">admin</a
				>
				{#if !data.authenticatedUser}
					<a
						class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white"
						href="/auth/login">Login</a
					>
				{:else}
					<a
						class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white"
						href="/auth/logout">Logout</a
					>
				{/if}
			</div>
		</div>
	</div>
</nav>

<!-- {JSON.stringify(data.user)} -->

<!-- {#if data.user}
	<div class="bg-green-500 py-2 text-center text-white">
		Welcome {data.user.email}
	</div>
{/if} -->

<!-- <div class="container mx-auto px-2"> -->
{@render children()}
<!-- </div> -->

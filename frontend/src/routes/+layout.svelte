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

<!-- <nav>
    <a href="/">home</a>
    <a href="/about">about</a>
    <a href="/blog">blog</a>
    <a href="/temp">temp</a>
</nav> -->

<nav class="bg-gray-800">
	<div class="px-2 sm:px-6 lg:px-12">
		<div class="relative flex h-16 items-center justify-between">
			<div class="flex space-x-4">
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'home'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					aria-current={activeButton === 'home'}
					href="/"
					onclick={() => (activeButton = 'home')}>Home</a
				>
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'about'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					href="/about"
					aria-current={activeButton === 'about'}
					onclick={() => (activeButton = 'about')}>About</a
				>
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'blog'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					href="/blog"
					aria-current={activeButton === 'blog'}
					onclick={() => (activeButton = 'blog')}>Blog</a
				>
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'temp'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					href="/temp"
					aria-current={activeButton === 'temp'}
					onclick={() => (activeButton = 'temp')}>Temp</a
				>
				<a
					class="rounded-md px-3 py-2 text-sm font-medium {activeButton === 'hero'
						? 'bg-gray-900 text-white'
						: 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
					href="/hero"
					aria-current={activeButton === 'hero'}
					onclick={() => (activeButton = 'hero')}>Hero</a
				>
			</div>
			<!-- make some icons that are all the way to the right -->
			<div class="flex space-x-4">
				<div class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">
					<a href="/admin">admin</a>
				</div>
				{#if !data.user}
					<div class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">
						<a href="/auth/login">Login</a>
					</div>
				{:else}
					<div class="rounded-md px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">
						<a href="/auth/logout">Logout</a>
					</div>
				{/if}
			</div>
		</div>
	</div>
</nav>

{#if data.user}
	<div class="bg-green-500 py-2 text-center text-white">
		Welcome {data.user.email}
	</div>
{/if}

<div class="container mx-auto px-2">
	{@render children()}
</div>
